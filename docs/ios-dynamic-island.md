# The Dynamic Island, the screen's corners, and the band above the page

Written 2026-08-17 against the working tree at `db8ae1e` (`main`), Xcode's
iPhoneSimulator **26.5** SDK, iOS **26.5** Simulator, device profile **iPhone
Air** (`com.apple.CoreSimulator.SimDeviceType.iPhone-Air`).

Each finding below is marked **VERIFIED** (read out of the shipped SDK, Apple's
own published text, or measured on a running build) or **INFERRED**.

---

## 1. What was wrong

`HalDisplay::presentIfNeeded` clears the whole output to the field colour
(`src/HalDisplay.cpp:1212`) and then places the panel top-aligned below the
reserved top band. On a pale page that field ran edge to edge, so above the page
there was 80 pt of white with the Dynamic Island sitting in it as an unattached
black pill. Owner, 2026-08-17: *"bring the rounded corners lower than dynamic
island so there's not a distracting hole above the panel."*

**Measured on the shipped build (VERIFIED)**, iPhone Air, 3x, window 420x912 pt
/ 1260x2736 px:

| thing | points | device px |
|---|---|---|
| Dynamic Island top edge | 20.0 | 60 |
| Dynamic Island bottom edge | **56.3** | 169 |
| Dynamic Island width | 123.7 | 371 |
| `safeAreaInsets.top` (via `SDL_GetWindowSafeArea`) | 74 (per `ios/README.md`) | 222 |
| `kTopReserve` floor, and so the reserved band | **80.0** | 240 |
| panel top edge | 83.7 | 251 |

So the band this app already reserves clears the Island's bottom edge by
**23.7 pt** without measuring the Island at all. That is the whole reason the fix
needs no Island API.

---

## 2. Is there a public API for the Dynamic Island / sensor housing frame?

**No. `safeAreaInsets` remains the only supported signal, and Apple says so
explicitly. (VERIFIED — Apple DTS.)**

Apple Developer Forums thread 802758, *"[iOS 26] Can no longer detect whether
iPhone has notch"*, DTS Engineer:

> We don't recommend you doing this and there's no first-party API that provides
> support for detecting whether a device has a notch or island.

The workarounds offered in that thread are a device-model table or
`window.safeAreaInsets.top > 20` — i.e. the same heuristic everyone has used
since the iPhone X. Nothing was added in iOS 17/18/26 to replace it.

Corroborating, from Apple's Human Interface Guidelines, **Layout** (fetched
2026-08-17 from `developer.apple.com/tutorials/data/design/human-interface-guidelines/layout.json`,
which is the page's own source; the rendered page is JS-only and does not fetch)
— **VERIFIED, quoted verbatim**:

> A *safe area* defines the area within a view that isn't covered by a toolbar,
> tab bar, or other views a window might provide. Safe areas are essential for
> avoiding a device's interactive and display features, like Dynamic Island on
> iPhone or the camera housing on some Mac models.

> **Respect key display and system features in each platform.** When an app or
> game doesn't accommodate such features, it doesn't feel at home in the platform
> and may be harder for people to use.

`WidgetKit`'s `DynamicIsland` type is the *Live Activity* presentation API — it
lets your activity render **into** the Island. It reports nothing about the
Island's frame to an ordinary app and is not usable here. (VERIFIED — it lives in
WidgetKit, not UIKit, and is a `View` builder.)

### 2a. Apple's guidance on content that must clear the Island

There is **no rule that content must clear it**; the rule is "use the safe area,"
and full-bleed is explicitly blessed. HIG **Layout**, verbatim (VERIFIED):

> **Prefer a full-bleed interface for your game.** Give players a beautiful
> interface that fills the screen while accommodating the corner radius, sensor
> housing, and features like Dynamic Island. If necessary, consider giving
> players the option to view your game using a letterboxed or pillarboxed
> appearance.

Worth recording because the old HIG *did* carry the opposite-sounding line —
"Don't mask or call special attention to key display features," which warned
against black bars and adornments around the sensor housing. **That text is gone
from the current Layout page** (VERIFIED: the words `mask`, `adorn`, `black bar`
and `call special attention` do not occur anywhere in `layout.json`). The current
guidance is only "respect the safe area," which the band below does — it *is* the
safe area, painted.

---

## 3. Getting the screen's corner radius without `UIScreen._displayCornerRadius`

**There is still no public property that hands back the number. (VERIFIED
against the SDK on disk.)**

- `UIScreen.h` in `iPhoneSimulator26.5.sdk` has no corner-radius property; the
  class is largely deprecated as of iOS 26 in favour of
  `view.window.windowScene.screen` and trait equivalents.
- `_displayCornerRadius` appears in `UIKit.tbd` only as the Swift symbols
  `UIMutableTraits.displayCornerRadius` and `UITraitDisplayCornerRadius` — and
  that trait carries an `_isPrivate` static and is **absent from the public
  `arm64-apple-ios-simulator.swiftinterface`**. It is SPI, not API.

**What iOS 26 *did* add is a way to get the right corner without ever seeing the
number** (VERIFIED — headers quoted from
`iPhoneSimulator26.5.sdk/.../UIKit.framework/Headers/UICornerRadius.h`):

```objc
API_AVAILABLE(ios(26.0), tvos(26.0), visionos(26.0))
@interface UICornerRadius : NSObject <NSCopying>
+ (instancetype)fixedRadius:(CGFloat)radius;
+ (instancetype)containerConcentricRadius;
+ (instancetype)containerConcentricRadiusWithMinimum:(CGFloat)minimum;
@end
```

applied through `UICornerConfiguration` (`+configurationWithUniformRadius:`,
`+capsule()`, per-corner variants) and set on `UIView.cornerConfiguration`.
SwiftUI's equivalents are `GeometryProxy.concentricCornerRadii` and
`ConcentricRectangle`. Apple's own framing is that these adapt "to the shape of
the window scene and the display itself" — the case
`_displayCornerRadius` used to be reached for.

### The probe, and its result (VERIFIED — measured, not reasoned)

`CrossPointAppearance_displayCornerRadius()`
(`ios/CrossPointAppearance.mm`) builds the recipe the SwiftUI writeups give: a
view exactly filling the window, `cornerConfiguration` set to a uniform
`containerConcentricRadius`, laid out, then `layer.cornerRadius` read back.

**It returns 0.** Logged from the running app:

```
[corner] display corner radius probe: 0.00 pt (window 420x912)
[bezel] band 240 px, corner 55.0 pt (fallback)
```

**INFERRED cause, with supporting evidence:** the concentric radius is resolved
below the CALayer the app owns, so there is nothing to read back on the client
side. The same launch logs BaseBoard registering
`BSCornerRadiusConfiguration` (`_topLeft`/`_topRight`/`_bottomLeft`/`_bottomRight`)
and FrontBoard registering `safeAreaCornerInsets` /
`safeAreaCornerInsetResolver` on `FBSSceneSettings` — i.e. the corner geometry is
scene settings pushed from the system, not a property UIKit writes onto your
layer. Treat "the number is not obtainable publicly" as the operating assumption.

**So there are exactly two honest options for a *number*:** a hardcoded value
(what `ScreenCorners`, `BezelKit` and every per-model table do, all of them via
the private API or a device list), or a fallback constant. This repo takes the
fallback: **55 pt**, `kCornerFallback` in `ios/CrossPointIOSShim.cpp`.

**Not taken, and worth knowing it exists:** if the corner ever has to be *exact*,
the way to get it is to stop asking for the number and let UIKit draw the shape —
a real `UIView` above SDL's view with `cornerConfiguration` set to
`containerConcentricRadius`. That costs a UIKit view in the render path and an
inverted mask (we need the sliver *outside* the arc, which a corner
configuration does not express), which is why the SDL fillet was preferred for a
change this size.

### `cornerCurve = .continuous`

Apple's display corners are a squircle, not a circular arc; `CALayer.cornerCurve
= .continuous` (iOS 13+) is what matches it, and it only applies to
`layer.cornerRadius` — it is a property of a *layer*, so it does nothing for
geometry drawn by hand. (VERIFIED: `cornerCurve` is on `CALayer`.) The band here
is drawn with SDL scanlines against a circular arc, so it is a circular corner,
not a squircle. At 55 pt the difference is a couple of device pixels of
fatness near the 45-degree point and is not visible against a black band.
**INFERRED** that it does not matter here; if the card's corner is ever compared
side by side with the glass, this is the first thing to fix.

---

## 4. What shipped

One band and two fillets, painted by the harness's own overlay:

- `ios/CrossPointIOSShim.cpp` — `paintTopBezel()`, called from `paintPad()`
  after the layout block. Fills `y = 0 .. g_topBezelPx` pure black, then knocks
  the field's two upper corners out to the same black with the inverse of
  `fillRoundRect`'s scanline arithmetic.
- `ios/CrossPointIOSShim.cpp` — `layoutPad()` publishes `g_topBezelPx`, which is
  the reserved top inset **only on a device with a cut-out**
  (`safeAreaInsets.top > 20 pt`). A home-button iPhone reports 20 and gets no
  band; it has no hole to hide and 80 pt of black would be a change nobody
  asked for.
- `ios/CrossPointAppearance.{h,mm}` — `CrossPointAppearance_displayCornerRadius()`,
  the public-API probe above. Returns 0 rather than a guess, so a zero is never
  mistaken for a measured square corner.

**Pure black, not a palette tone**, because the point is that the Island stops
reading as a separate shape and the Island is `#000000`.

**CORRECTION, 2026-08-17 — dark mode DID have the hole.** The first version of
this document claimed it did not, on the reasoning that a `#121212` field is
"nearly invisible" against the Island. The owner reported otherwise ("dark has
that problem") and he is right: `#121212` against `#000000` is a 6% luminance
step that a screenshot flattens and an OLED does not — the field EMITS and the
Island is pixels off, so the pill reads as a hole cut in the page. With a CRT
palette it is plainer still, because those papers are tinted (Green CRT is
`001A00`) and a pure-black pill sits in a coloured ground.

The claim was made without measuring, and repeated. Measured now, dark
appearance with `PAPER_DARK=001A00`, on the shipped build:

```
row    0 (  0.0 pt): (0, 0, 0)      <- the band; the Island disappears into it
row  240 ( 80.0 pt): (0, 26, 0)     <- the page's own paper begins
```

So the band is painted in BOTH appearances and dark is fixed by the same change
— it was simply never true that dark had nothing to fix.

iPad is untouched: `layoutPadTablet()` returns before the phone branch, so
`g_topBezelPx` stays 0. Desktop is untouched: this whole file is iOS-only.

### Verified on device profile (screenshots, iPhone Air, iOS 26.5 Simulator)

| | before | after |
|---|---|---|
| field at `y = 0`, centre column | `#FFFFFF` | `#000000` |
| first non-black row, centre column | 0 | **240** (= 80.0 pt) |
| first non-black row, `x = 2` (the fillet) | 0 | **377** |
| bottom-most row | unchanged white | unchanged white |
| Island visible as a pill | **yes** | no |

---

## Sources

- [Apple Developer Forums 802758 — "[iOS 26] Can no longer detect whether iPhone has notch"](https://developer.apple.com/forums/thread/802758) (DTS Engineer: no first-party API)
- [HIG — Layout](https://developer.apple.com/design/human-interface-guidelines/layout) (quotes taken from its `layout.json` source, 2026-08-17)
- [UICornerRadius](https://developer.apple.com/documentation/uikit/uicornerradius-swift.struct) / [UICornerConfiguration](https://developer.apple.com/documentation/uikit/uicornerconfiguration-c.class) / [UIView.cornerConfiguration](https://developer.apple.com/documentation/uikit/uiview/cornerconfiguration-7l0ja)
- [What's New in UIKit 26 — Sebastian Vidal](https://sebvidal.com/blog/whats-new-in-uikit-26/) (containerConcentric, "previously possible through UIScreen's private `_displayCornerRadius`")
- [How to Get the Screen Corner Radius in iOS 26 with concentricCornerRadii](https://swiftuisnippets.wordpress.com/2026/08/06/how-to-get-the-screen-corner-radius-in-ios-26-with-concentriccornerradii/) (the fill-the-screen recipe this repo's probe implements)
- [ScreenCorners](https://github.com/kylebshr/ScreenCorners) and [Finding the Real iPhone X Corner Radius](https://kylebashour.com/posts/finding-the-real-iphone-x-corner-radius) (the private-API/hardcoded state of the art)
- [BezelKit](https://markbattistella.com/writings/2023/introducing-bezelkit/) (per-model radius table)
- [safeAreaInsets](https://developer.apple.com/documentation/uikit/uiview/safeareainsets), [WidgetKit DynamicIsland](https://developer.apple.com/documentation/widgetkit/dynamicisland)


---

## Update 2026-08-17: the page runs up to the cut-out

Owner: **"extend top up to dynamic island (too short currently)."**

The band was 80 pt because `layoutPad` took `max(safeArea.top, kTopReserve)` and
`kTopReserve = 80` always won on a cut-out phone. Measured on the iPhone Air the
Island ends at 56.3 pt, so the page began **23.7 pt below it** — dead black with
nothing in it.

The safe area is exactly the line iOS puts below a cut-out, so on a cut-out
device it is now taken as-is:

| | before | after |
|---|---|---|
| safe area top | 68.0 pt | 68.0 pt |
| page top | 80.0 pt | **68.0 pt** |
| gap below the Island | 23.7 pt | **11.7 pt** |

A phone with **no** cut-out reports the classic 20 pt status bar and keeps the
80 pt reserve — moving its page up 60 pt is a change nobody asked for.

**What this gives up**, recorded because it was a deliberate choice being
reversed: the 80 pt reserve was sized to clear a floating Picture-in-Picture
window parked in a top corner (`mockups/pip-envelope.html`). At the safe area
the page no longer clears one.

**The remaining 11.7 pt is Apple's own margin below the Island**, not slack of
ours. Closing it means drawing inside the safe area — permitted, since the
Island itself ends higher, but it is a deliberate step past the supported line
and no API reports where the Island actually ends (see above). Not taken without
being asked.

---

## Update 2026-08-18: the page starts 8 pt lower, and the corner is measured now

Owner: **"move panel down (without moving others) to be more clear of rounded
corners at top."**

The 2026-08-17 change above put the page's top edge at the safe area, 68.0 pt.
That is clear of the Dynamic Island, but it is **not** clear of the screen's
rounded corners — and this write-up had no measurement of those corners at all,
only the 55 pt fallback the fillet is drawn with.

### The display's corner shape is measurable after all — off the simulator profile

**VERIFIED, measured, not inferred.** Every simulator device type ships Apple's
own display mask as a vector PDF:

```
/Library/Developer/CoreSimulator/Profiles/DeviceTypes/iPhone Air.simdevicetype/
  Contents/Resources/1506CF9E-8F5F-48D9-91CA-E852368519A5.pdf   # profile.plist: framebufferMask
```

`MediaBox [0 0 2520 5472]` — half-device-pixel units, i.e. 2 units per device
pixel and 6 per point on this 3x phone. Its single path is the rounded-rectangle
squircle the framebuffer is masked with. Flattened and converted to points, the
top-left corner runs **88.45 pt across and 88.17 pt down** — far past the 55 pt
the fillet assumes, because a continuous corner's extent is much wider than the
circular radius of the same corner. How far in the screen edge still sits at a
given depth:

| depth from the top | screen edge inset |
|---|---|
| 55.0 pt | 1.71 pt |
| 60.0 pt | 1.03 pt |
| 68.0 pt (the old page top) | 0.39 pt |
| 72.0 pt | 0.21 pt |
| **76.0 pt (the new page top)** | **0.10 pt** — under a third of a device pixel |
| 88.2 pt | 0.00 pt — the curve ends |

This does **not** overturn §3: nothing here is available to the app at runtime,
on the Simulator or on hardware. It is a host-side measurement of one device
profile, which is exactly what is needed to choose a constant.

### What changed

`ios/CrossPointIOSShim.cpp`, `layoutPad()`: on a cut-out device the top inset is
now `safeTop + kCornerClear`, `kCornerClear = 8.0f`.

8 pt is one step of the pad's 8 pt grid (owner ruling 2026-08-11), and it is the
smallest such step that reaches a depth where the display's own curve is done to
within a third of a device pixel — so the black band beside the page's top
corners reads as an even margin rather than a pinched crescent. It stays 4 pt
above the old 80 pt `kTopReserve`, so 2026-08-17's "extend top up to dynamic
island" is trimmed, not undone.

### Nothing else moved — decoded, iPhone Air, 3x

| | before | after |
|---|---|---|
| page top edge (first non-black centre row) | 204 px = **68.0 pt** | 228 px = **76.0 pt** |
| presented panel rect | `1160x1740 at 50,206` | `1148x1722 at 56,229` |
| panel bottom edge | 1946 px = 648.7 pt | 1951 px = 650.3 pt |
| pad **bottom** row top edge | 2418 px = **806.0 pt** | 2418 px = **806.0 pt** |
| POWER / palette chip rows | 2514, 2603, 2606, 2610 px | **identical** |
| pad **top** row top edge | 2016 px = 672.0 pt | 2020 px = 673.3 pt |

The page loses the 8 pt off its own **height**, not off the pad's space: on this
phone the panel is height-limited (the fit comes from `availH`, not the width),
so a deeper top band shrinks the panel and its bottom edge — which is what the
pad hangs off (`SimulatorOverlay::panelBottomPx`) — stays put. The 4 device
pixels the top row does move are the residue of the scale quantum (6 px of panel
height per step) plus the derived bottom band shrinking with the panel; 1.3 pt
against the 8 pt the page moved.

**On a WIDTH-limited phone this would not hold** — there the slack sits below
the page, a deeper top band pushes the whole panel down, and the pad follows.
No profile in use today is width-limited (every one is short of height). That is
the line in `layoutPad` to revisit if one appears.

### Open, not taken

The fillet is still drawn at the **55 pt circular** fallback while the measured
mask is an 88 pt-extent squircle, so the page's corner is a slightly different
shape from the glass's. Invisible against a black band, and outside what was
asked for; recorded here so the next person does not re-measure it.
