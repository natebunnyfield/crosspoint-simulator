import XCTest

// Queries CrossPoint X3 through the REAL accessibility runtime -- the same
// out-of-process channel Speak Screen and VoiceOver use -- rather than the
// in-process walk the app's own diagnostics do. The device logs (builds 46-47)
// proved the container ANSWERS correctly in-process while assistive tech never
// consulted it; this asks Apple's channel directly.
final class CrossPointAXTests: XCTestCase {
  func testReaderPageIsServedToTheAXRuntime() throws {
    let app = XCUIApplication(bundleIdentifier: "com.natebunnyfield.crosspoint.x3")
    app.launchEnvironment["CROSSPOINT_SIM_INPUT_SCRIPT"] = "2500:DOWN;3100:ENTER;5000:ENTER"
    app.launch()
    // Give the firmware time to boot and open the book (script above).
    Thread.sleep(forTimeInterval: 8)

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

  func testSpeakScreenModeAddsTheReadingPageElement() throws {
    let app = XCUIApplication(bundleIdentifier: "com.natebunnyfield.crosspoint.x3")
    app.launchEnvironment["CROSSPOINT_SIM_INPUT_SCRIPT"] = "2500:DOWN;3100:ENTER;5000:ENTER"
    app.launchEnvironment["CROSSPOINT_SIM_FORCE_SPEAKSCREEN"] = "1"
    app.launch()
    Thread.sleep(forTimeInterval: 8)

    // The line elements must survive unchanged...
    XCTAssertGreaterThan(app.staticTexts.count, 0, "line elements vanished in Speak Screen mode")
    // ...and the page-protocol element must appear alongside them.
    let page = app.descendants(matching: .any)["crosspoint.reading-page"]
    print("AXPROBE reading-page exists: \(page.exists) frame=\(page.exists ? String(describing: page.frame) : "-")")
    XCTAssertTrue(page.exists, "the UIAccessibilityReadingContent page element is not served")
  }
}
