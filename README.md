# Youtube load & transcribe service
CLI version of a service

 **Table of content:**
- [Project description](#item-one)
- [Specifications](#item-two)
- [Build](#item-three)


<a id="item-one"></a>

### Description
The service is about to easily get the transcript of an any YouTube object 
(video, shorts, live) by loading subtitles or in case of missing -> transcribing using Whisper models locally on machine.

On the current service state - CLI mode only is available, that is providing the following functionality:  
1. Download an audio by YouTube link
2. Download a video by YouTube link
3. Download a text by YouTube link. In case of missing subtitles on YouTube -> transcribe locally using Whisper
4. All the above for an YouTube channel link (be careful - it loads all channel videos)
5. Transcribe file (audio or video) using Whisper

<a id="item-two"></a>

### Specifications

- Service is develop using Python.  
- Almost all operations are asynchronous.
- This version does not support external configuration options (TBD)
- **! REQUIRES .env file with "YOUTUBE_API" variable**

<a id="item-three"></a>

### Build

- Install the package by `make install` (it also loads whisper models in case of missing on your machine)
- Run a service by `make`
- You can uninstall all dependencies using `make uninstall_all_dependencies`