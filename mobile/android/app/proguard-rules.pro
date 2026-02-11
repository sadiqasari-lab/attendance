# React Native
-keep class com.facebook.hermes.** { *; }
-keep class com.facebook.jni.** { *; }

# React Native Camera
-keep class com.google.android.cameraview.** { *; }

# React Native Maps
-keep class com.google.android.gms.maps.** { *; }

# OkHttp
-dontwarn okhttp3.**
-dontwarn okio.**
-keep class okhttp3.** { *; }

# React Native Encrypted Storage
-keep class com.emeraldsanto.encryptedstorage.** { *; }

# React Native Device Info
-keep class com.learnium.RNDeviceInfo.** { *; }

# Prevent stripping of native methods
-keepclassmembers class * {
    @com.facebook.react.bridge.ReactMethod *;
}

# Keep ViewManagers
-keep class * extends com.facebook.react.uimanager.ViewManager { *; }

# Keep annotation
-keepattributes *Annotation*
-keepattributes SourceFile,LineNumberTable
-keepattributes Signature

# Arabic/RTL support
-keep class androidx.appcompat.** { *; }
