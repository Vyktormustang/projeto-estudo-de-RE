# Permissões

| permissão | risco | evidência de uso no DEX (amostra) |
|---|---|---|
| ACCESS_ADSERVICES_AD_ID | low/unknown |  |
| ACCESS_ADSERVICES_ATTRIBUTION | low/unknown |  |
| ACCESS_NETWORK_STATE | low |  |
| ACCESS_SUPERUSER | low/unknown |  |
| ACCESS_WIFI_STATE | low |  |
| AUTHENTICATE_ACCOUNTS | medium |  |
| DELETE_PACKAGES | high |  |
| ENFORCE_UPDATE_OWNERSHIP | low/unknown |  |
| FOREGROUND_SERVICE | low |  |
| GET_ACCOUNTS | medium | AccountManager cannot be null, Landroid/accounts/AccountManager;, Landroid/accounts/AccountManagerCallback; |
| GET_PACKAGE_SIZE | low |  |
| INSTALL_PACKAGES | critical |  |
| INTERNET | low |  |
| MANAGE_ACCOUNTS | medium |  |
| MANAGE_EXTERNAL_STORAGE | high |  |
| PACKAGE_USAGE_STATS | high | Landroid/app/usage/UsageStatsManager; |
| POST_NOTIFICATIONS | low |  |
| QUERY_ALL_PACKAGES | high | getInstalledApplications, queryIntentActivities |
| RECEIVE_BOOT_COMPLETED | low |  |
| RECORD_AUDIO | high |  |
| REQUEST_DELETE_PACKAGES | medium |  |
| REQUEST_INSTALL_PACKAGES | high | ACTION_VIEW_CONSTRUCTOR_SIGNATURE, ACTION_VIEW_STATES_KEY, EXPANDED_ACTION_VIEW_ID |
| UPDATE_PACKAGES_WITHOUT_USER_ACTION | critical |  |
| USE_BIOMETRIC | low/unknown |  |
| USE_CREDENTIALS | medium |  |
| USE_FINGERPRINT | low/unknown |  |
| WAKE_LOCK | low |  |
| WRITE_EXTERNAL_STORAGE | medium | getExternalStorageDirectory |
| com.google.android.c2dm.permission.RECEIVE | low/unknown |  |
| com.google.android.finsky.permission.BIND_GET_INSTALL_REFERRER_SERVICE | low/unknown |  |
| com.google.android.gms.permission.AD_ID | low/unknown |  |
| com.uptodown.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION | low/unknown |  |

declaradas pelo app: com.uptodown.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION
