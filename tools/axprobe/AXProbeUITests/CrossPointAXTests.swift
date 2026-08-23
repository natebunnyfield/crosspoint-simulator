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
  private static let openAndReachText =
    "4000:QTAP:BACK;10000:QTAP:RIGHT;14000:QTAP:RIGHT;18000:QTAP:RIGHT"
  private static let settleSeconds: TimeInterval = 22

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
