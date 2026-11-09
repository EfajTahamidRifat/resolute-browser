plugins {
    // AGP 9 compiles Kotlin itself (built-in Kotlin). Declaring the Kotlin plugin here
    // (not applied) only selects the Kotlin compiler version, matching GeckoView's.
    id("com.android.application") version "9.1.1" apply false
    id("org.jetbrains.kotlin.android") version "2.4.20" apply false
}
