# Contributing or Developing this Plugin

This section is very much a work in progress.

## Getting a Trace via Android Emulator

There are a few steps you need to follow to get this all to work...

### Emulator Setup

1. Create an emulator using a non-Google Play Store version
1. Download a Dreo app APK from any of the various Google Play Store downloaders

### Frida to Defeat Certificate Pinning - Part 1
The Dreo app uses certificate pinning. You can use *Frida* to get around that.  Full instructions are here: https://httptoolkit.com/blog/frida-certificate-pinning. The following are the steps I followed:
. Download and extract the Frida Android Server from here:  https://github.com/frida/frida/releases1.
1. Windows can extract the `.xz` archive format.
1. Copy the binary and start Frida on your device as follows:
    ```bat
    # Copy the server to the device
    adb push ./frida-server-$version-android-$arch /data/local/tmp/frida-server
    #        ^Change this to match the name of the binary you just extracted
    
    # Enable root access to the device
    adb root
    
    # Make the server binary executable
    adb shell "chmod 755 /data/local/tmp/frida-server"
    
    # Start the server on your device
    adb shell "/data/local/tmp/frida-server &"
    ```
1. Install Frida on your PC using Python
    ```bat
    pip install frida-tools
    ```

1. You can test this by running `frida-ps -U`. This will connect to the server via USB (-U) and list the details over every running process on the target device. If this shows you a list of processes, you're set

### Setup Fiddler Classic as a Proxy
1. Use Fiddler Classic (http://www.fiddlertool.com) to get a network trace to see what the Dreo app is doing. I won't document here how to setup Fiddler as a proxy or do SSL decryption; Fiddler documentation is pretty good.
1. Create a Fiddler rule where this line is added to `OnBeforeRequest`

    ```
    oSession.oRequest["ua"] = "dreo/2.5.12 (sdk_gphone64_arm64;android 13;Scale/2.625)";
    ```
1. Get the Fiddler root CA from the options and use certutil.exe to get the PEM version.  You'll need it later.
   
### Frida to Defeat Certificate Pinning - Part 2
1. Clone the following repo which contains a bunch of handy scripts: https://github.com/httptoolkit/frida-interception-and-unpinning
1. Navigate to that cloned repo
1. Modify `config.js` appropriately. Note you'll need the base 64 cert from Fiddler.
1. Start Frida on your PC.  This will cause the app on the emulator to restart with correct settings.

    ```
    frida -U -l ./config.js -l ./native-connect-hook.js -l ./android/android-proxy-override.js -l ./android/android-system-certificate-injection.js  -l ./android/android-certificate-unpinning.js -l ./android/android-certificate-unpinning-fallback.js -f com.hesung.dreo
    ```

