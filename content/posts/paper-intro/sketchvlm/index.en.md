---
# weight: 1
title: "SketchVLM: Letting a VLM Draw Its Reasoning on the Image"
date: 2026-08-08
lastmod: 2026-08-08
draft: false
description: "A walkthrough of SketchVLM: with no retraining, a coordinate grid, XML commands and Bézier smoothing let a VLM annotate the image so its answers are verifiable."
featuredImage: "featured-image.png"

tags: ["Vision Language Model", "Large Language Model", "Prompting"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## Introduction

Ask today's vision language models (VLMs) a visual reasoning question and you will usually get back a wall of text: whether there's enough engine oil, which bucket the ball will land in, how to get through the maze. The problem is, how do you confirm any of it is true? There is no direct correspondence between a text answer and the image, the model may simply have guessed right, and you have no way to see what it based its judgement on.

- [Paper link (arXiv:2604.22875)](https://arxiv.org/abs/2604.22875)

That verification gap is exactly what SketchVLM sets out to close. It lets a VLM answer not only in text but by drawing lines, boxes, and numbers directly onto the original image, laying its thought process out where you can see it. More importantly, none of this requires retraining the model, and none of it damages the original image — the annotations are an overlaid vector layer that can be removed at any time.

This article follows SketchVLM's technical thread: how it gets the model to draw *accurately* on the canvas, how it turns drawing into a structured instruction format the model can emit reliably, how it uses mathematics to turn jittery coordinate points into smooth curves, and finally how the framework performs on real tasks — along with the problems it hasn't solved yet.

{{< admonition type="abstract" title="Key Takeaways (TL;DR)" >}}
- **Non-destructive annotation**: an SVG vector layer sits on top of the original image, so every original pixel is preserved intact.
- **Training-free**: model parameters are untouched; visual prompting such as a coordinate grid plus a carefully designed system prompt is enough to give existing VLMs drawing ability.
- **Visual chain-of-thought**: the reasoning process is drawn out so annotations and the text answer can be checked against each other — annotation–text alignment averages 95.5%, far above the 28.6%–46.8% of fine-tuned models.
{{< /admonition >}}

## "How do you know you're right?" — the VLM verification gap

Top-tier models like GPT-4o and Gemini already generate fluent text, but the moment a task requires spatial reasoning tied precisely to pixel positions, the cracks show. A user asks a question about car maintenance or a physical trajectory, the model returns a long paragraph of description, and that paragraph is very hard to map precisely onto a location in the image. (For just how hard the underlying visual representation problem is for multimodal models, see the earlier walkthrough of [Cambrian-1](../cambrian-1-a-fully-open-vision-centric-exploration-of-multimodal-llms/).)

Hallucination makes it worse. The model may get the text right while having merely "guessed" it, or having looked at the wrong place and coincidentally produced the correct answer. Pure text output leaves users with no way to work backwards and check the model's reasoning — you can only choose to believe it or not.

SketchVLM's approach is to prise open one corner of that black box. Answering the same question — "how do I read this oil dipstick?" — a conventional VLM gives you a paragraph of explanation, while SketchVLM marks the safe-level position directly on the photo of the dipstick and walks you through it step by step.

{{< image src="figure1.png" alt="On the left, a conventional VLM answers a question about checking engine oil with text only; on the right, SketchVLM marks the dipstick position and the safe level directly on the photo, guiding the user step by step." caption="Fig. 1 — For a question like \"is there enough engine oil?\" that can only be settled by looking at the image, a conventional chatbot gives text only, while SketchVLM draws the key points directly on the photo. (Source: original paper)" >}}

## Existing annotation approaches all hit a ceiling

Before SketchVLM, getting a VLM to "point at" what matters in an image fell into roughly three approaches, each with an obvious limit.

- **Coordinate point output** (e.g. Molmo, MoonDream): cheap to compute, but it can only emit points — no continuous trajectories or shapes — so any task needing a box or a connecting line is out of reach.
- **Image editing** (e.g. Nano Banana Pro): visually intuitive, but it modifies the original pixels directly. That is destructive, and it readily hallucinates content unrelated to the original image.
- **Task-specific fine-tuning** (e.g. ViLaSR, ThinkMorph): decent on the tasks it was trained for, but accuracy collapses on an unseen task type such as a new maze layout — generalisation is poor. (Fine-tuning strategies for multimodal models are a research direction of their own; see [Tuning LayerNorm in Attention](../layernorm-tuning-multi-modal/).)

The paper compares these lines of work systematically, and the crux is which of them simultaneously offers *training-free* operation and *vector-overlay, non-destructive* annotation.

{{< image src="table1.png" alt="The paper's comparison table of annotation methods, listing for each whether it is training-free, supports multi-turn dialogue, requires an input image, allows free-form drawing, and whether its annotation type is vector overlay or image editing." caption="Table 1 — SketchVLM compared with other sketching models and methods; the key differences are the \"training-free\" and \"vector overlay (non-destructive)\" columns. (Source: original paper)" >}}

"Non-destructive" sounds like a nice-to-have, but in some settings it is a hard requirement. Picture medical imaging or an industrial repair site: if the annotation process covers up a crack or a component in the original photo, the AI assistant becomes actively dangerous. SketchVLM overlays an SVG vector layer, so every pixel of the original image stays 100% intact — the annotation is just a transparency sheet laid on top, which the user can edit or peel off entirely at any time.

## SketchVLM's three design pillars

Put those problems and limitations side by side and SketchVLM's design goals become quite clear, summarised in three points:

- **Non-destructive annotation**: an SVG vector layer over the original image, leaving the source data fully intact.
- **Training-free**: the whole framework is model-agnostic and requires no retraining; a carefully designed system prompt is enough to give a strong existing VLM the ability to draw.
- **Visual chain-of-thought**: the model's reasoning is drawn out directly, so the annotations and the model's text answer agree with each other and can be cross-verified.

The next few sections unpack how each of these is realised: first how the model draws *accurately*, then how drawing is turned into stable instruction output, and finally how the jittery lines it produces get smoothed into clean curves.

## The coordinate grid: hand the model a ruler first

A VLM has no built-in sense of precise coordinates, so asking it to intuit the right spot on an image is a tall order. SketchVLM's answer is not to trust that intuition but to hand the model an external ruler first — a coordinate grid.

Concretely, the system does not draw grid lines onto the original image's pixels (that would obscure the content). Instead it uses an image library such as Pillow to append a white margin to the left and bottom of the image, marks tick numbers along that margin, and aligns the ticks with the image resolution — for a 1000x1000 image, the ticks run from 0 to 1000. The benefit is that every original pixel is untouched: the model sees "original image plus a bolt-on ruler" rather than a picture chopped up by grid lines.

This is also why the authors call the technique *visual prompting* rather than mere image preprocessing: it does not touch the model's parameters at all, only changes the image content on the input side to induce more regular behaviour. It's a bit like handing a person with normal eyesight but no sense of direction a map with a grid drawn on it — the grid is the prompt that lets them describe a route precisely.

Interestingly, not every model takes to it. The paper's ablation shows that adding the grid sharply reduces Gemini-3-Pro's error on the connect-the-dots task, while GPT-5's response is flat and even slightly worse. The presumed reason is that the GPT family already has a strong internal normalised coordinate system (0 to 1000), so layering an external grid on top may visually interfere with that built-in sense of position.

{{< image src="table3.png" alt="Ablation table comparing, in single-turn mode, the effect of including or omitting the coordinate grid prompt on the accuracy of Gemini-3-Pro and GPT-5 across several tasks." caption="Table 3 — Adding the coordinate grid does not affect all models the same way: Gemini-3-Pro performs best with the grid, while GPT-5 performs better without it. (Source: original paper)" >}}

## Turning drawing into structured instructions: XML syntax and coordinate encoding

With an external coordinate system in place, the next question is: how does the model state "I want to draw a line here" clearly, stably, and in a form a program can parse reliably?

### Why XML instead of JSON

SketchVLM drops JSON in favour of XML-style tags, for a very practical reason: language models are noticeably more stable at generating *paired tags* (an opening tag matched by a closing tag) than nested JSON structures, and the backend can extract the content precisely with a simple regular expression instead of handling malformed JSON. Each stroke is wrapped in `<sN>...</sN>`, where N is the stroke index; coordinates use a format like `x500y100` that glues x and y together, so a coordinate pair compresses into a single token and the model is less likely to mis-pair x with y when emitting them.

### The basic drawing primitives

On top of this syntax, the model can describe several basic drawing actions:

| Shape type | Representation | When to use |
| --- | --- | --- |
| Free-form drawing | A run of consecutive coordinate points | Complex paths, e.g. a bounce trajectory |
| Straight line | Start and end point only | Pointing, simple lines |
| Rectangle / box | Four corner points in order | Boxing out an object's extent |
| Arrow | Split into shaft and head | When direction must be explicit |
| Text label | `<text>` plus an anchor coordinate | Numbers or names; the model decides font size and colour by judging contrast |

Drawing rectangles involves a small trick worth mentioning: at each of the four corners, the system requires the model to emit the same coordinate twice in a row. Because Bézier curves later connect these points into arcs, without the trick the square's corners would be smoothed into rounded ones; repeating a coordinate at the same point effectively tells the smoothing algorithm to "pause here", preserving the sharp corner. It's a neat example of solving a geometry-rendering problem through instruction design.

Besides coordinates, the model must attach a `t` value to each point, ranging from 0 to 1, representing how far along the stroke that point sits. The parameter itself does not affect position, but the Bézier smoothing algorithm downstream needs it to work out the ordering of the points and the tangent direction — without `t`, the algorithm cannot tell how to thread the points into a smooth, directed curve.

### Task-specific instruction constraints

The authors also design matching instruction constraints per task: object counting may only place a number at the centre point and must not draw boxes; part labelling is forced to use a predefined label list so the model doesn't invent names; maze navigation requires the model to "draw first, answer second", making the annotation the model's own scratchpad that supports step-by-step reasoning rather than a post-hoc explanation.

## From jittery points to smooth lines: Bézier curves and least squares

The coordinate points a VLM emits are typically discrete and slightly jittery; connecting them with straight segments produces visibly jagged shapes that look nothing like a hand-drawn line. This section is about how SketchVLM turns "imperfect points" into "curves that look right".

The cubic Bézier curve is the core tool here. What makes it special is that you don't have to describe every point on the line — four control points define a smooth curve. Two of them are the endpoints P0 and P3, which the line is guaranteed to pass through; the other two, P1 and P2, do not lie on the line and act more like magnets — P1 sets the direction the line leaves the start point, P2 the direction it enters the end point, each pulling the curve's overall course toward itself.

The problem is that the VLM gives you *points on the path*, while a Bézier curve needs *control points (the magnets)* — two different things, requiring a bridge. That bridge is least squares. The procedure is to collect the string of coordinates the model produced along with their `t` values, posit a Bézier curve, compute the sum of squared distances between that curve and the points, and use calculus to find the P1 and P2 coordinates that minimise this error. Put plainly, least squares acts as a translator: it converts the jittery path points the model tossed out into the two magnet positions that mathematically fit those points best.

Take predicting a falling object's trajectory: the model only needs to emit three key points along the ball's bounce, and least squares fills in the arc the parabola should have, making the trajectory look physically plausible. This brings an incidental engineering benefit too — because a handful of key points suffices to describe a complex shape, the model's XML output is shorter, latency drops, and API costs fall with it.

## Making annotations legible — and able to teach

Once the drawing is accurate and stable, two practical questions remain: how do these annotations stay clearly visible against any background? And when a task requires guiding the user step by step, how does the model keep multi-turn dialogue coherent?

### Visibility: model-side decisions plus render-side protection

For visibility, SketchVLM uses a dual mechanism of model-side decision plus render-side protection. On colour, the model analyses the image's background colour and specifies a sufficiently high-contrast colour code directly in the XML. On size, text labels and line thickness scale dynamically with how much of the frame the object occupies. At render time, text uniformly gets a contrasting outline (rather like the black outline common in game subtitles), ensuring annotations stay legible even against a busy background.

### Single-turn and multi-turn modes

As for dialogue, SketchVLM supports both single-turn and multi-turn modes, suited to rather different scenarios:

| Property | Single-turn | Multi-turn |
| --- | --- | --- |
| Behaviour | Emits all annotations and the answer at once | Draws one stroke, says one thing, waits for feedback |
| Best for | Quick diagnosis, physical trajectory prediction | Software how-to guidance, complex repair instructions |
| System cost | Low, a single API call | High, repeated image upload and processing |

{{< image src="figure3.png" alt="A side-by-side diagram of the single-turn and multi-turn generation flows, showing the same physical reasoning sample producing all annotations and the answer at once in single-turn mode, versus producing one annotation per turn and reusing previous annotations in multi-turn mode." caption="Fig. 3 — Single-turn mode generates all annotations and the answer in one call; multi-turn mode produces one annotation per turn and feeds the previous annotations (as both rendered image and text record) back into the model until it gives a final answer. (Source: original paper)" >}}

Multi-turn mode has an easily overlooked detail: on every turn the model must receive not only the image drawn so far but also the XML text record of every previous annotation. The reason is that from the rendered image alone, the model struggles to identify the exact pixel coordinates at a stroke's endpoint, so the next stroke easily fails to connect; the text record supplies precise numeric memory while the image supplies spatial sense, and only together do multi-turn annotations stay coherent. The authors also add a "one stroke per turn" gate, forcing the model to draw a single stroke each turn and breaking complex operations into steps a user can digest — especially useful in teaching contexts, since the frame never fills up with a confusing pile of annotations at once.

A concrete example is guiding a user to remove a background in Photoshop: each turn the model receives the current screenshot and uses labelled arrows and highlight boxes to indicate where to click next, teaching the operation one step at a time.

{{< image src="figure12.png" alt="A multi-turn tutorial example in which the model annotates each turn's screenshot with labelled arrows and highlight boxes to show the user, step by step, how to remove a background in image editing software." caption="Fig. 12 — A multi-turn example of SketchVLM guiding a user through removing an image's background: each turn marks what to do next based on the current screen. (Source: original paper)" >}}

## Experimental results: seven tasks, three metrics

The paper tests SketchVLM on seven tasks: connect-the-dots, object counting, drawing shapes, part labelling, maze navigation, physical intuition (predicting which container a ball falls into), and advanced physics (simulating drop and bounce trajectories). The range is broad, from pure spatial precision to path reasoning that requires planning.

The evaluation looks at more than whether the final answer is right. The authors define three dimensions: the accuracy of the answer itself, whether the annotation is smooth and well-formed (annotation quality), and *annotation–text alignment* — that is, whether looking only at the annotation, without the text answer, is enough to infer the model's conclusion. The authors stress that the third metric matters most, because it tests whether the annotation genuinely reflects the model's thinking rather than being pretty decoration.

In the numbers, SketchVLM beats image-editing baselines (such as Nano Banana Pro) on reasoning accuracy by up to 28.5 percentage points; annotation quality is about 1.48x better than fine-tuned models (ViLaSR, ThinkMorph); and annotation–text alignment averages 95.5%, far above the fine-tuned models' 28.6% to 46.8%.

{{< image src="table2.png" alt="An accuracy table across physical and spatial reasoning tasks, comparing SketchVLM, its variants, and fine-tuned models on multiple tasks." caption="Table 2 — SketchVLM maintains competitive accuracy while producing visual reasoning traces; fine-tuned sketching models perform near random chance on these tasks. (Source: original paper)" >}}

Part labelling yields another detail worth noting: the label positions SketchVLM places land very close to the correct locations, beating the baseline at every tolerance level, with the gap down to just a few pixels.

{{< image src="table4.png" alt="A comparison table of SketchVLM's label position accuracy against the baseline across different error tolerances." caption="Table 4 — Labels placed by SketchVLM land very close to the correct location, outperforming the baseline at every tolerance level by a margin of only a few pixels. (Source: original paper)" >}}

## Limitations and open problems

SketchVLM performs well, but the authors themselves point out several practical limits. The first is small objects: the paper honestly reports that for very small objects, SketchVLM's annotation precision falls slightly short of simply emitting a coordinate box — related to VLMs being inherently less sensitive to small pixel regions.

The second is that interaction is still incomplete. Multi-turn dialogue currently has no "undo" or "erase"; if the model draws something wrong, it cannot make a local correction the way a real whiteboard discussion would, and can only keep drawing. The third is that only static images are supported so far — the annotation mechanism has not been extended to video. All three read as clear directions for future work rather than fundamental design flaws.

## Conclusion

The core problem SketchVLM tackles is simple: VLMs are increasingly articulate, but what they say cannot be verified. Its solution comes down to three things. First, using least squares to fit Bézier curves to the model's jittery output coordinates, converting fuzzy visual perception into precise geometric lines — the mathematical basis for drawing smooth curves from very few points. Second, using XML tags and a coordinate grid to establish a "visual thinking language" the model can emit stably and the backend can parse reliably, with no retraining whatsoever. Third, insisting on SVG vector overlay instead of pixel modification, keeping the original image intact.

Across all three metrics — accuracy, annotation quality, and annotation–text alignment — SketchVLM clearly surpasses existing image-editing and fine-tuning approaches. Its weakest spots are annotation precision on very small objects and the missing interaction details like undo and erase. Overall, this is solid work that takes "let the model draw to explain itself" from a concept to a practical, training-free, non-destructive framework.
