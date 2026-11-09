import java.util.Properties

plugins {
    id("com.android.application")
}

// Keys come from environment variables (GitHub Actions secrets) or, for local
// builds, from local.properties. They are never committed to the repo.
val localProps = Properties().apply {
    val f = rootProject.file("local.properties")
    if (f.exists()) f.inputStream().use { load(it) }
}
fun secret(name: String): String =
    (System.getenv(name) ?: localProps.getProperty(name) ?: "").replace("\"", "")

android {
    namespace = "com.resolute.browser"
    compileSdk = 37

    defaultConfig {
        applicationId = "com.resolute.browser"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "0.0.1"

        buildConfigField("String", "HELIUS_RPC_URL", "\"${secret("HELIUS_RPC_URL")}\"")
        buildConfigField("String", "ALCHEMY_RPC_URL", "\"${secret("ALCHEMY_RPC_URL")}\"")
        buildConfigField("String", "LIFI_API_KEY", "\"${secret("LIFI_API_KEY")}\"")
        buildConfigField("String", "REOWN_PROJECT_ID", "\"${secret("REOWN_PROJECT_ID")}\"")
        buildConfigField(
            "String", "CONFIG_URL",
            "\"https://raw.githubusercontent.com/EfajTahamidRifat/resolute-browser/main/config/partners.json\""
        )
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }

    buildFeatures {
        buildConfig = true
        viewBinding = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}


dependencies {
    // GeckoView (Firefox engine). Update this version regularly for security fixes.
    implementation("org.mozilla.geckoview:geckoview:159.0.20261102144711")

    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("com.google.android.material:material:1.12.0")
}
