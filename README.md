BlenderBQ
=========

A Leap Motion and voice-control interface for Blender.

Check out our [demo video](https://wwww.youtube.com/watch?v=jP8xYVJ3uNI)!

## Features

### Object mode

Enter object mode by saying "object".
In this mode, you can use two gestures:

- `grab` to move the object around the scene
- `pinch` inwards or outwards to scale the object

The "center" voice command will place the object back at the origin.
The "reset" voice command acts as "center" but also cancels any applied rotation.

### Camera control

Several voice commands are available to control the view:

- "over" (or "**above**"), "under" (or  "below")
- "left", "right"
- "front", "back"
- "camera"

### Pottery mode

Enter pottery mode by saying "pottery".
In this mode, you can use two gestures:

- `swipe` left or right to start rotating the object in this direction. Repeating the movement speeds up rotation.
- `point` with your finger to start

Several modifiers are avaiable:

- The "add" voice command will switch the brush to adding matter to the object
- The "substract" voice command will switch the brush to removing matter from the object
- The "noob" voice command will toggle between symetric sculpting and local scuplting

### Paint mode

Enter paint mode by saying "paint".

In this mode, there's only one gesture : keep your hand flat with your five fingers spread out. Move your hand to select the desired color in the RGB space.

### Misc

At any time, use the "sleep" and "wake" voice commands to disable or enable voice recognition.

## Required

- python 2.7 (the Leap Motion API only supports Python 2.x for now)
- A working Blender install (tested with Blender 2.70)
- A working Leap Motion install
- Voice recognition packages (optionnal):
    - [gstreamer runtime](http://gstreamer.freedesktop.org/)
    - gst-python
    - [CMUSphinx](http://cmusphinx.sourceforge.net/wiki/download/) (sphinxbase-0.8)
    - PocketSphynx (pocketsphinx-0.8)

## How to run

Run these commands in a UNIX terminal.

1. Plug in your Leap Motion and make sure it is detected correctly by your system.
2. `cd` to the BlenderBQ directory
3. `python server.py`
4. `blender -P blender.py [filename]` (use the `filename` parameter if you want to open a file directly)
5. In Blender, using the command palette (shortcut: `spacebar`), launch the "BBQ operator"

If everything is working correctly, you should lose mouse control over the scene while the BBQ operator is running.

