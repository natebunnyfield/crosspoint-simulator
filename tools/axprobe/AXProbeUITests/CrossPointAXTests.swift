import XCTest

// Queries CrossPoint X3 through the REAL accessibility runtime -- the same
// out-of-process channel Speak Screen and VoiceOver use -- rather than the
// in-process walk the app's own diagnostics do. The device logs (builds 46-47)
// proved the container ANSWERS correctly in-process while assistive tech never
// consulted it; this asks Apple's channel directly.
//
// THE BOOK OPENS ON A PAGE WITH NO TEXT, and every test here pages past it.
// `wrap0000.xhtml` is a cover wrapper: an <img> and nothing else, which the
// reader renders as an entirely blank panel and the firmware correctly
// captures as an empty page. A probe that stops there measures nothing and
// reads as a failure of the exposure -- which is exactly the trap the
// 2026-08-23 investigation fell into for its first four runs. `QTAP:BACK`
// opens the book from Home; each `QTAP:RIGHT` is one page forward
// (ReaderUtils::detectPageTurn -- page-forward is the RIGHT front button, not
// DOWN).
final class CrossPointAXTests: XCTestCase {
  // `200:QTAP:BACK:2500` holds Back across the boot routing check, which is
  // main.cpp's own escape hatch to Home (:957) and the only lever XCUITest has
  // -- it can set environment variables and nothing else, and the alternative
  // lever (readerActivityLoadCount in state.json) needs the card written before
  // launch. Without it the boot destination alternates run to run, so `BACK`
  // means "open the book" on one run and "leave the reader" on the next.
  // Measured 2026-08-23; docs/headless-qa.md §4.
  //
  // Then Back opens the book, the LEFTs page to the FRONT of it, and one RIGHT
  // steps off the cover onto the first page with prose on it.
  //
  // Paging back first is what makes "a body page" mean the same page every run.
  // The app resumes wherever the last run left it, and this book's front matter
  // is a run of nearly empty pages -- a half-title of 19 characters, a title
  // page of 26 -- so a fixed number of RIGHTs from an unknown start lands on
  // one of those about as often as on prose, and the >40-character assertion
  // then fails on a page the app rendered and published perfectly. Measured
  // twice on 2026-08-23 before this was pinned down.
  private static let openAndReachText: String = {
    var s = "200:QTAP:BACK:2500;5000:QTAP:BACK"
    for i in 0..<8 { s += ";\(11000 + i * 2200):QTAP:LEFT" }
    return s + ";29000:QTAP:RIGHT"
  }()
  private static let settleSeconds: TimeInterval = 40

  private func launchIntoABodyPage(forceSpeakScreen: Bool) -> XCUIApplication {
    let app = XCUIApplication(bundleIdentifier: "com.natebunnyfield.crosspoint.x3")
    app.launchEnvironment["CROSSPOINT_SIM_INPUT_SCRIPT"] = Self.openAndReachText
    if forceSpeakScreen { app.launchEnvironment["CROSSPOINT_SIM_FORCE_SPEAKSCREEN"] = "1" }
    app.launch()
    Thread.sleep(forTimeInterval: Self.settleSeconds)
    return app
  }

  func testReaderPageIsServedToTheAXRuntime() throws {
    let app = launchIntoABodyPage(forceSpeakScreen: false)

    let texts = app.staticTexts
    print("AXPROBE staticTexts count: \(texts.count)")
    for i in 0..<min(texts.count, 8) {
      let el = texts.element(boundBy: i)
      print("AXPROBE [\(i)] label=\"\(el.label)\" frame=\(el.frame)")
    }
    // Any element of the published page proves the AX server carries it.
    XCTAssertGreaterThan(texts.count, 0,
      "the AX runtime serves ZERO static texts -- the page never reaches Apple's channel")
  }

  // THE SPEAK SCREEN REGRESSION TEST.
  //
  // Speak Screen consumes exactly one thing (measured across builds 42-54): a
  // full UITextInput adoption on the accessibility element, the WWDC26-219
  // pattern. This asserts that element is (a) present in the out-of-process AX
  // tree, (b) carrying the page's text rather than an empty string, and (c)
  // framed over the panel rather than off-screen or collapsed -- the three ways
  // "No speakable content could be found on the screen" has been produced by
  // this app, none of which a compile or an in-process dump can see.
  func testSpeakScreenIsServedThePageWithASaneFrame() throws {
    let app = launchIntoABodyPage(forceSpeakScreen: true)

    // The line elements must survive unchanged -- VoiceOver reads those, and
    // they are the confirmed-working half.
    XCTAssertGreaterThan(app.staticTexts.count, 0, "line elements vanished in Speak Screen mode")

    let page = app.descendants(matching: .any)["crosspoint.page-textinput"]
    print("AXPROBE page-textinput exists: \(page.exists)")
    XCTAssertTrue(page.exists, "the UITextInput page view is not served to the AX runtime")

    // (b) NON-EMPTY TEXT. The view vends the page through accessibilityValue as
    // well as the protocol, so an empty value means Speak Screen would find an
    // element with nothing in it -- indistinguishable, from the owner's chair,
    // from no element at all.
    let value = (page.value as? String) ?? ""
    print("AXPROBE page-textinput value: \(value.count) chars -- \"\(value.prefix(60))\"")
    XCTAssertGreaterThan(value.count, 40,
      "the page view is served but carries no text (\(value.count) chars)")

    // (c) A SANE FRAME. Two separate failures live here: a frame collapsed to a
    // point (a zero scale, or geometry answered before the first present) and a
    // frame off the screen (bottom-edge read as an origin, or a panel placed
    // outside the window). Both are silent -- assistive tech simply skips the
    // element.
    let frame = page.frame
    let screen = app.windows.element(boundBy: 0).frame
    print("AXPROBE page-textinput frame=\(frame) screen=\(screen)")
    XCTAssertGreaterThan(frame.width, 100, "page frame is collapsed horizontally")
    XCTAssertGreaterThan(frame.height, 100, "page frame is collapsed vertically")
    XCTAssertTrue(frame.intersects(screen), "the page frame is entirely off-screen")
  }

  // THE COVER, THROUGH APPLE'S OWN CHANNEL (owner ruling 2026-08-23).
  //
  // Every other test here pages PAST the cover, because a cover wrapper is an
  // <img> and nothing else and the firmware correctly captures an empty page.
  // This one stops on it deliberately. Until the ruling, an empty capture meant
  // no element at all, so the first page of every book -- the one an owner sees
  // the moment they open it -- answered Speak Screen with "No speakable content
  // could be found on the screen" while the whole chain behind it was healthy.
  //
  // What it must now vend is something TRUE about the page: the book's name,
  // from the recents entry the firmware wrote before the first render, and the
  // fact that this page has no text on it. Never invented prose, and never the
  // previous page's -- so the assertion is on the fallback's own words, not
  // merely on the element being non-empty.
  //
  // Getting there is the fiddly half, and none of it is guesswork:
  //
  //  - `200:QTAP:BACK:2500` HOLDS Back across the boot routing check, which is
  //    main.cpp's own escape hatch to Home (:957). Without it the boot
  //    destination alternates -- a run killed inside the reader leaves
  //    readerActivityLoadCount=1 and the next launch lands on Home instead of
  //    the book -- and a fixed script then means something different every
  //    other run. docs/headless-qa.md carries the measurement.
  //  - Then Back opens the book from Home, and RIGHT-then-LEFTs walk to the
  //    front of it. The app resumes wherever the last run left off, so the
  //    surplus LEFTs are the margin; at the start of the book they are no-ops.
  //  - The RIGHT before them is load-bearing: a page TURN onto the cover is
  //    what publishes it. If the reader were already sitting on the cover,
  //    every LEFT would be a no-op, nothing would publish, and the element
  //    under test would never be built.
  func testCoverPageSpeaksTheBookInstead() throws {
    let app = XCUIApplication(bundleIdentifier: "com.natebunnyfield.crosspoint.x3")
    var script = "200:QTAP:BACK:2500;5000:QTAP:BACK;10000:QTAP:RIGHT"
    for i in 0..<10 { script += ";\(16000 + i * 2200):QTAP:LEFT" }
    app.launchEnvironment["CROSSPOINT_SIM_INPUT_SCRIPT"] = script
    app.launchEnvironment["CROSSPOINT_SIM_FORCE_SPEAKSCREEN"] = "1"
    app.launch()
    Thread.sleep(forTimeInterval: 44)

    let page = app.descendants(matching: .any)["crosspoint.page-textinput"]
    print("AXPROBE cover page-textinput exists: \(page.exists)")
    XCTAssertTrue(page.exists,
      "a page with no text vends NO element at all -- the cover is silent again")

    let value = (page.value as? String) ?? ""
    print("AXPROBE cover page-textinput value: \"\(value)\"")
    print("AXPROBE cover page-textinput frame=\(page.frame)")
    XCTAssertFalse(value.isEmpty, "the cover's element is served but carries nothing")
    XCTAssertTrue(value.contains("This page has no text"),
      "the cover vends \"\(value)\" -- not the textless-page fallback. Either the "
      + "reader is not on the cover (page back further), or the card could not "
      + "name the book (recent.json / state.json).")
    // The frame is the panel's, exactly as a text page's is: an element iOS
    // cannot place is an element it may skip.
    XCTAssertGreaterThan(page.frame.width, 100, "cover page frame is collapsed horizontally")
    XCTAssertGreaterThan(page.frame.height, 100, "cover page frame is collapsed vertically")

    // AND NOT A SUPPLEMENT. There are no words on this page, so there are no
    // line elements over the panel either -- VoiceOver's experience of a blank
    // page is byte-identical to what it was before the fallback existed.
    let overPanel = app.staticTexts.allElementsBoundByIndex.filter {
      $0.frame.intersects(page.frame) && !$0.label.isEmpty
    }
    print("AXPROBE cover line elements over the panel: \(overPanel.count)")
    XCTAssertEqual(overPanel.count, 0,
      "a page with no words produced line elements: \(overPanel.map { $0.label })")
  }

  // The same, but with the REAL system flag rather than the app's override.
  //
  // `CROSSPOINT_SIM_FORCE_SPEAKSCREEN` exists because ios/README.md recorded
  // that Speak Screen could not be turned on in the simulator. That was WRONG,
  // and the belief is a large part of why the 2026-08-09 arc cost twelve
  // TestFlight builds: the pane in Settings is named "Speak Screen" but the
  // preference behind it is `com.apple.Accessibility SpeakThisEnabled`, and
  // writing it makes UIAccessibilityIsSpeakScreenEnabled() return true in the
  // simulator (measured 2026-08-23). This test therefore exercises the SHIPPED
  // branch -- the one an owner's phone takes -- and not just the override.
  //
  // Enable it before running the suite:
  //   xcrun simctl spawn <udid> defaults write com.apple.Accessibility \
  //       SpeakThisEnabled -bool true
  //
  // SKIPS rather than fails when the flag is off, so a run on a simulator that
  // was not prepared reports honestly instead of blaming the app.
  func testRealSpeakScreenFlagReachesThePageView() throws {
    let app = launchIntoABodyPage(forceSpeakScreen: false)
    let page = app.descendants(matching: .any)["crosspoint.page-textinput"]
    guard page.exists else {
      throw XCTSkip("""
        Speak Screen is off on this simulator, so the app correctly builds no \
        page view. Enable it with: xcrun simctl spawn <udid> defaults write \
        com.apple.Accessibility SpeakThisEnabled -bool true
        """)
    }
    let value = (page.value as? String) ?? ""
    print("AXPROBE real-flag page-textinput value: \(value.count) chars")
    XCTAssertGreaterThan(value.count, 40,
      "the real Speak Screen flag built a page view with no text in it")
  }
}
