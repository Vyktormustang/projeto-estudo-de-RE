# Componentes do manifest

| tipo | quantidade |
|---|---|
| activity | 64 |
| provider | 4 |
| receiver | 11 |
| service | 15 |

exportados: **14** de 94

## Deep links / schemes

| scheme | host | path | componente |
|---|---|---|---|
| https | www.uptodown.com | /preregister-available | com.uptodown.activities.MainActivity |
| https | market.android.com |  | com.uptodown.activities.MainActivity |
| https | play.google.com |  | com.uptodown.activities.MainActivity |
| http | play.google.com |  | com.uptodown.activities.MainActivity |
| https | dw.uptodown.com | /dwn | com.uptodown.activities.MainActivity |
| file | * | .*.xapk | com.uptodown.activities.MainActivity |
| content | * | .*.xapk | com.uptodown.activities.MainActivity |
| file | * | .*.apkm | com.uptodown.activities.MainActivity |
| content | * | .*.apkm | com.uptodown.activities.MainActivity |
| file | * | .*.apks | com.uptodown.activities.MainActivity |
| content | * | .*.apks | com.uptodown.activities.MainActivity |

## Componentes exportados sem `permission`

| tipo | nome | base da classificação |
|---|---|---|
| activity | com.uptodown.activities.MainActivity | EXPLÍCITO no manifest |
| activity | com.uptodown.tv.ui.activity.TvMainActivity | EXPLÍCITO no manifest |
| activity | com.uptodown.core.activities.InstallerActivity | EXPLÍCITO no manifest |
| activity | com.uptodown.activities.SearchActivity | EXPLÍCITO no manifest |
| activity | com.inmobi.cmp.presentation.components.CmpActivity | EXPLÍCITO no manifest |
| receiver | com.uptodown.receivers.BootDeviceReceiver | EXPLÍCITO no manifest |
| receiver | com.uptodown.receivers.MyAppUpdatedReceiver | EXPLÍCITO no manifest |
| receiver | com.uptodown.receivers.DownloadNotificationReceiver | EXPLÍCITO no manifest |
| receiver | com.uptodown.receivers.DownloadUpdateNotificationReceiver | EXPLÍCITO no manifest |

## Providers

| provider | authorities |
|---|---|
| androidx.core.content.FileProvider | com.uptodown.provider |
| com.google.firebase.provider.FirebaseInitProvider | com.uptodown.firebaseinitprovider |
| androidx.startup.InitializationProvider | com.uptodown.androidx-startup |
| com.squareup.picasso.PicassoProvider | com.uptodown.com.squareup.picasso |
