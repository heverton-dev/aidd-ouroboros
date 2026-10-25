"""Gerador determinístico de APK simulado para testes E2E do AIDD Ouroboros.

Cria um arquivo ZIP com extensão .apk contendo um AndroidManifest.xml em texto plano,
com permissões explícitas para validação do extrator estático aidd-rea-app-android.
"""

from pathlib import Path
import zipfile

SAMPLE_MANIFEST = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.ouroboros.sampleapp"
    android:versionCode="1"
    android:versionName="1.0.0">

    <uses-sdk android:minSdkVersion="24" android:targetSdkVersion="34" />

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />

    <application
        android:allowBackup="true"
        android:label="OuroborosSample"
        android:supportsRtl="true">
        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
"""


def generate_sample_apk(output_path: Path) -> Path:
    """Gera o arquivo APK fixture contendo o AndroidManifest.xml."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("AndroidManifest.xml", SAMPLE_MANIFEST.strip())
        zf.writestr("resources.arsc", b"DUMMY_RESOURCES")
        zf.writestr("classes.dex", b"DUMMY_DEX")
    return output_path


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "sample_app.apk"
    generate_sample_apk(out)
    print(f"Fixture gerado em: {out}")
