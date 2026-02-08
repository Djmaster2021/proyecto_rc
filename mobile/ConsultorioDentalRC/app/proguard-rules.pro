# Add project specific ProGuard rules here.
# You can control the set of applied configuration files using the
# proguardFiles setting in build.gradle.
#
# For more details, see
#   http://developer.android.com/guide/developing/tools/proguard.html

# If your project uses WebView with JS, uncomment the following
# and specify the fully qualified class name to the JavaScript interface
# class:
#-keepclassmembers class fqcn.of.javascript.interface.for.webview {
#   public *;
#}

# Uncomment this to preserve the line number information for
# debugging stack traces.
#-keepattributes SourceFile,LineNumberTable

# If you keep the line number information, uncomment this to
# hide the original source file name.
#-renamesourcefileattribute SourceFile

# Retrofit / Gson metadata commonly required at runtime
-keepattributes Signature,RuntimeVisibleAnnotations,RuntimeVisibleParameterAnnotations,AnnotationDefault,InnerClasses,EnclosingMethod
-keep class retrofit2.** { *; }
-keep class okhttp3.** { *; }
-dontwarn okhttp3.**
-dontwarn okio.**
-keep class com.google.gson.** { *; }
-keep class * extends java.lang.Enum { *; }

# Keep model fields used by Gson reflection
-keepclassmembers class ** {
    @com.google.gson.annotations.SerializedName <fields>;
}
