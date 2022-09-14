
<div align="center">

# yt-mused
#### Finally, the YouTube Music Premium experience for free.

</div>

<p style="text-align:justify">
XDA Team Vanced did a terrific job of making YouTube Premium more accessible.
But even to the day of their shutdown the question remained:
Why can't you download the music too?
This is where yt-mused fuses together ytmusicapi and yt-dlp alongside other processing and tagging libraries in order to bring your YouTube Music library to your device for offline entertainment.
</p>

<div align="center">

[Installation](#installation) •
[Configuration](#configuration) •
[Getting started](#getting-started) •
[Sync directly to your Android phone](#sync-directly-to-your-android-phone) •
[Pictures](#pictures) •
[Further information](#further-information)


</div>

<br>

### Installation
- Get [yt-dlp](https://github.com/yt-dlp/yt-dlp)


- Get [ffmpeg](https://ffmpeg.org/download.html)


- Get yt-mused:

      git clone https://github.com/nosch41/yt-mused.git
  - Navigate to folder `yt-mused` and install requirements:

        cd yt-mused
        pip install -r requirements.txt

- [Set up ytmusicapi](https://ytmusicapi.readthedocs.io/en/latest/setup.html) and place your personal `headers_auth.json` file inside `yt-mused/app`

<br>

### Configuration
Inside `yt-mused/app` you will find `settings.ini`, which you can optionally configure to your liking.
You can set a custom location for the music downloads and modify the application's syncing behavior in many ways.
There is also an option to enable multiprocessing in order to achieve greater speeds, amongst other things.

<br>

### Getting started
Once everything is set up, simply run the `main.py` file contained in `yt-mused/app/`.

    cd app  
    python3 main.py

<br>

#### Sync directly to your Android phone
If you're like me and mainly listen to music on your phone and you don't want to copy the files to your phone everytime you synced them,
syncing them directly to your Android phone is possible following these steps:

1. Copy the `yt-mused` folder to your phone 
2. Inside `settings.ini` choose an appropriate path for your music, e.g. `/storage/emulated/0/Music`
3. Install and set up [Termux](https://play.google.com/store/apps/details?id=com.termux)
   1. Inside Termux install python and the required packages
4. Run the `main.py` file contained in `yt-mused/app/`
5. See your music appear in your favorite music app (I use Poweramp)

In order to be able to invoke the synchronization easily without much of a hassle,
it is recommended to have a simple sync button on your homescreen that does everything automatically.

6. Get [Tasker](https://play.google.com/store/apps/details?id=net.dinglisch.android.taskerm)
7. Get [Termux:Tasker](https://play.google.com/store/apps/details?id=com.termux.tasker)
8. Place the command that runs yt-mused inside a bash script.
9. Using Tasker and the Termux:Tasker plugin you choose any trigger (e.g. a button on your homescreen) to run the bash script and sync your music

<br>

### Pictures
I have been using this implementation flawlessly for the last two years. Here is how it looks like on my phone.

<div align="center">

### **Homescreen shortcut**<br>
<img src="https://i.postimg.cc/fRnrqrfP/hs.jpg" alt="Homescreen shortcut" width=250px/><br>
*Syncing at the click of a button*

<br>

### **Playlist / Folder view**<br>

<img src="https://i.postimg.cc/SKmtkY57/pl.jpg" alt="Playlist/Folder view" width=250px/><br>
*See your playlists as you would in YouTube Music*

<br>

### **Inside "Your likes"**<br>

<img src="https://i.postimg.cc/QMSYtxZL/liked.jpg" alt='Inside "Your likes"' width=250px/><br>
*All your liked songs, tags and covers included.* 

</div>

<br>

### Further information

The file format used by mused is MPEG-4  (`.m4a`).
Under the hood the files are named after their respective YouTube video ID, which facilitates quick syncing.
Using a music player however, the songs are displayed intuitively with the title, artist and album tag as well as the album cover as an embedded thumbnail.

Please don't hesitate to ask further questions!
