# hedgcoxekhav
Python Flask Service Interface for AV Scene Switching

Simple webinterface frontend to AVMatrix SDI router and Behringer X18R audio mixer.

You can edit the application settings and available scenes in the `config.json` file.

OSC commands and scene settings to the Behringer X18R audio mixer are handled through the utilies found here:

[XAIRUtilities](https://sites.google.com/site/xairutilities/)

The patched version of pmaillot's original source code for the CLI utilities is found here:

[X32Utilities](https://github.com/jgruber/X32-Behringer)

A Docker file is included which can build a container image. 

`docker build -t khavmixer:latest .`

Running the container:

`docker run --name khavmixer -p 3100:3100 -d --rm khavmixer:latest`

Then open a browser to:

`http://localhost:3100`

The `/var/lib/hedgcoxekhav/static` directory should be volume mounted to a local directory to maintain the screnes and web layout from the local file system.

## config.yaml

Scene resources and the configuration of the service is are found in the 

```
static/scenes
```

directory.

The `config.yaml` file has several global values:

`WEB_SERVICE_PORT`: the TCP port the web service creates a listener

`WEB_SERVICE_DEBUG`: produce debug messages in to stdout or log

`AV_SWITH_IP`: The AVMatrix switch IP address

`AV_SWITHC_PORT`: The AVMatrix UDP port to send config messages (default: 7000)

`AUDIO_MIXER_IP`: The Behringer XAir Audio Mixer IP

```
DEFAULT_AUDIO_SCENE:
    file: [the XAir saved scene file in the scene directory to load when starting]
    description: Default setting for public meetings
```
The `INIT_AUDIO_SCENE` XAir scene file is used to initialize the mixer to remove and old configuration that might linger.

You shouldn't change the `INIT_AUDIO_SCENE` setting unless you know why.

```
INIT_AUDIO_SCENE:
    file: Initialized.scn
    description: Scene used to initialize the XAir mixer
```

The `MUTE_SCENE` is sent to the XAir mixer before each change to try to prevent any changes which might cause feeback.

The default `MUTE_SCENE` zeros out all channel faders and aux sends.

```
MUTE_SCENE:
    file: Mute.scn
    description: Mute all channel faders and sends
```

`XAIRSETSCENE`: The CLI command to use to set the XAir scene.

In the `bin` directory there are zip files for amd64 and Raspberry Pi 64 bit architectures. If you want to run this on any other platform you can compile the CLI commands from

https://github.com/jgruber/X32-Behringer

`XAIRCMD`: The CLI command to use to send specific OSC commands to the XAir mixer.

`IMAGE_HTML_PATH`: The path to your images. Default is `scenes/images`.

`LIVELYNESS_CHECK_SECS`: How often to send status requests to the devices to check reachability.

`scenes`: a YAML list of scene objects to display a tile to load.

A scene object looks like this:

```
scene_playlist_name:
    file: [The XAir saved scene in the scenes directory]
    description: [The scene description]
    videochannels:
        - input: '[input number]'
          output: '[comma separated list of output numbers]'
        - input: '[input number]'
          output: '[comma separated list of output numbers]'
    audioscene: [Audio scene index name to which as the status for the active scene set]
```

An Example with two defined scenes would look like this:

```
scenes:
  001_Default:
    file: 001_1_Meeting.scn
    imgagefile: 1_Meeting.png
    description: Default setting for public meetings
    videochannels:
    - input: '1'
      output: '1,2,3,4,5,6,7'
    - input: '2'
      output: '8'
    audioscene: Default
  002_2_Meetings_Classroom_2_Mics:
    file: 002_2_Meetings_Classroom_2_Mics.scn
    imgagefile: 2_Meetings_Classroom_2_Mics.png
    description: Classroom has its own meeting with both Wireless Microphones
    videochannels:
    - input: '1'
      output: '1,2,3,5,6,7'
    - input: '2'
      output: '8'
    - input: '3'
      output: '4'
    audioscene: 2_Meetings_Classroom_2_Mics
```
