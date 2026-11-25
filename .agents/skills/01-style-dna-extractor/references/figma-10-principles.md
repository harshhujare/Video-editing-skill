# The 10 Principles of the Arthur Brooks Minimal Style

Reference specification for classifying extracted reference frames and Figma style boards.

| Principle ID | Name | Visual Anatomy | Motion & Camera Signature | Typography Rules |
| :--- | :--- | :--- | :--- | :--- |
| `P1_CAPTION` | On-Screen Captions (A-Roll) | Talking-head A-roll full frame; dual-font captions in lower third (`top: 68%`). | Jump-cut A-roll with 30ms audio padding; 6-frame spring scale-in per word group. | `<= 5` words per block. 1–2 bold keywords centered (`72–88px`, Inter Bold or Playfair Bold Italic); supporting words (`34–42px`, Inter Regular) in top/bottom gaps. |
| `P2_BROLL_TEXT` | Textured B-Roll with Text | Stock action clip desaturated `-25%`, contrast `+10%`, outer 20% edge blur + dark vignette, 15% paper grain. | Subtle slow push-in or handheld drift inside `<CameraRig>`. | Dual-font caption cluster centered optically (`top: 46%`). |
| `P3_PAINTING` | Painting Animations | Classical public-domain painting inside feathered brush-stroke mask over rough white/cream paper texture. | Fast camera slide-in (`cubic-bezier(0.16, 1, 0.3, 1)`, ~18 frames) with paper texture moving inside `<CameraRig>`. | Descriptive dual-font text hugging the outer contour of the painting's focal subject. |
| `P4_LINE_TEXT` | Line and Text Animations | Accent cobalt-blue (`#1E5EFF`, `strokeWidth: 6`) SVG path on black or white paper-textured canvas. | `strokeDashoffset` reveal; `<CameraRig>` tracks the leading tip of the line. | Typography blocks interrupt the line path at exact break coordinates; line resumes after text. |
| `P5_LINE_ILLUSTRATION` | Line and Illustration Animations | (a) Horizontal blue line with white node dots (`r=10`), text above, stippled illustrations below; OR (b) Zigzag vertical/diagonal blue line with alternating side objects. | Camera pans horizontally along nodes or side-to-side down the zigzag path. | Concise phase labels above nodes or opposing alternating illustrations. Minimum 90-frame hold after reveal. |
| `P6_QUOTE_SCENE` | Text-Centric Quote Scenes | Rough white or cobalt-blue paper texture (`paper_rough_white.png` / `paper_cobalt_blue.png`) with oversized opening `“` and closing `”` marks (`180px`, `0.25` opacity). | Slow subtle scale drift (`1.00 -> 1.03`) with paper texture bound to `<CameraRig>`. | Centered philosophical punchline combining Inter and Playfair Display Bold Italic. Both `“` and `”` are mandatory. |
| `P7_CENTER_ILLUSTRATION` | Center Illustration Scenes | Noisy, stippled abstract illustration or rough-cloth character side profile in lower-center (`top: 45%–95%`). | Stepped or spring entry; minimum 90-frame hold after settle so artwork registers. | Dual-font text arranged in a radial arc or balanced upper-half cluster around illustration edges. |
| `P8_SIDE_ILLUSTRATION` | Side Illustration & Text Scenes | Split screen: abstract character or rough-cloth semicircle anchored flush against left or right edge. | Slide-in from screen edge; optional rotating circular text ring. | Balanced dual-font typography on the opposite half of the frame. |
| `P9_OBJECT_CALLOUT` | Object and Text Callouts | Single isolated story object or background-removed PNG cutout centered over paper texture. | 12-frame stepped stop-motion reveal mask. | Contextual callout labels positioned around the object perimeter. |
| `P10_DARK_GRAPH` | Graph and Statistics Scenes | Charcoal-black textured canvas (`#0D0F12`) with thin glowing white grid (`rgba(255,255,255,0.12)`). | Animated curve (stair-step or flat line) led by a glowing `#1E5EFF` sphere tracked by `<CameraRig>`. | Minimal axis/phase labels; speaker keywords appear near key inflection vertices. |

## Core Classification Heuristics

- **Never misclassify `P1_CAPTION` vs `P2_BROLL_TEXT`**: `P1` shows the speaker's face on A-roll; `P2` shows external desaturated/vignetted stock action footage.
- **Check Quotation Marks for `P6_QUOTE_SCENE`**: Only classify as `P6` when oversized framing quotes (`“ ... ”`) and a solid paper backdrop carry a takeaway sentence.
- **Texture Motion Verification**: Note whether the paper texture moves with the camera (`camera_bound: true`)—this is mandatory for later Remotion replication.
