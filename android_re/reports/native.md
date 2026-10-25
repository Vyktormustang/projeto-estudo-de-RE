# Bibliotecas nativas (ELF)

| path | bytes | arch | exports | imports | JNI |
|---|---|---|---|---|---|
| lib/arm64-v8a/libandroidx.graphics.path.so | 10096 | EM_AARCH64/64bit | 1 | 7 | 0 |
| lib/arm64-v8a/libdatastore_shared_counter.so | 7112 | EM_AARCH64/64bit | 9 | 10 | 4 |
| lib/arm64-v8a/libuptodown-native.so | 5240 | EM_AARCH64/64bit | 4 | 4 | 4 |
| lib/arm64-v8a/libutd-services-native.so | 4272 | EM_AARCH64/64bit | 1 | 3 | 1 |
| lib/armeabi-v7a/libandroidx.graphics.path.so | 7252 | EM_ARM/32bit | 1 | 8 | 0 |
| lib/armeabi-v7a/libdatastore_shared_counter.so | 4416 | EM_ARM/32bit | 9 | 8 | 4 |
| lib/armeabi-v7a/libuptodown-native.so | 3836 | EM_ARM/32bit | 4 | 5 | 4 |
| lib/armeabi-v7a/libutd-services-native.so | 3112 | EM_ARM/32bit | 1 | 4 | 1 |
| lib/x86/libandroidx.graphics.path.so | 9284 | EM_386/32bit | 1 | 7 | 0 |
| lib/x86/libdatastore_shared_counter.so | 5148 | EM_386/32bit | 9 | 7 | 4 |
| lib/x86/libuptodown-native.so | 4344 | EM_386/32bit | 4 | 4 | 4 |
| lib/x86/libutd-services-native.so | 3236 | EM_386/32bit | 1 | 3 | 1 |
| lib/x86_64/libandroidx.graphics.path.so | 10760 | EM_X86_64/64bit | 1 | 7 | 0 |
| lib/x86_64/libdatastore_shared_counter.so | 6224 | EM_X86_64/64bit | 9 | 7 | 4 |
| lib/x86_64/libuptodown-native.so | 5224 | EM_X86_64/64bit | 4 | 4 | 4 |
| lib/x86_64/libutd-services-native.so | 4288 | EM_X86_64/64bit | 1 | 3 | 1 |

## Entradas JNI

- `androidx.datastore.core.NativeSharedCounter#nativeTruncateFile` (lib/arm64-v8a/libdatastore_shared_counter.so)
- `androidx.datastore.core.NativeSharedCounter#nativeCreateSharedCounter` (lib/arm64-v8a/libdatastore_shared_counter.so)
- `androidx.datastore.core.NativeSharedCounter#nativeGetCounterValue` (lib/arm64-v8a/libdatastore_shared_counter.so)
- `androidx.datastore.core.NativeSharedCounter#nativeIncrementAndGetCounterValue` (lib/arm64-v8a/libdatastore_shared_counter.so)
- `com.uptodown.util.NativeApiKey#getAuthApikey` (lib/arm64-v8a/libuptodown-native.so)
- `com.uptodown.util.NativeApiKey#getAuthApikeyLite` (lib/arm64-v8a/libuptodown-native.so)
- `com.uptodown.util.NativeApiKey#getAuthApikeyOpenAppStore` (lib/arm64-v8a/libuptodown-native.so)
- `com.uptodown.util.NativeApiKey#getAuthApikeyDelta` (lib/arm64-v8a/libuptodown-native.so)
- `com.uptodown.services.utils.NativeConst#getApiKeySeed` (lib/arm64-v8a/libutd-services-native.so)
- `androidx.datastore.core.NativeSharedCounter#nativeTruncateFile` (lib/armeabi-v7a/libdatastore_shared_counter.so)
- `androidx.datastore.core.NativeSharedCounter#nativeCreateSharedCounter` (lib/armeabi-v7a/libdatastore_shared_counter.so)
- `androidx.datastore.core.NativeSharedCounter#nativeGetCounterValue` (lib/armeabi-v7a/libdatastore_shared_counter.so)
- `androidx.datastore.core.NativeSharedCounter#nativeIncrementAndGetCounterValue` (lib/armeabi-v7a/libdatastore_shared_counter.so)
- `com.uptodown.util.NativeApiKey#getAuthApikey` (lib/armeabi-v7a/libuptodown-native.so)
- `com.uptodown.util.NativeApiKey#getAuthApikeyLite` (lib/armeabi-v7a/libuptodown-native.so)
- `com.uptodown.util.NativeApiKey#getAuthApikeyOpenAppStore` (lib/armeabi-v7a/libuptodown-native.so)
- `com.uptodown.util.NativeApiKey#getAuthApikeyDelta` (lib/armeabi-v7a/libuptodown-native.so)
- `com.uptodown.services.utils.NativeConst#getApiKeySeed` (lib/armeabi-v7a/libutd-services-native.so)
- `androidx.datastore.core.NativeSharedCounter#nativeTruncateFile` (lib/x86/libdatastore_shared_counter.so)
- `androidx.datastore.core.NativeSharedCounter#nativeCreateSharedCounter` (lib/x86/libdatastore_shared_counter.so)
- `androidx.datastore.core.NativeSharedCounter#nativeGetCounterValue` (lib/x86/libdatastore_shared_counter.so)
- `androidx.datastore.core.NativeSharedCounter#nativeIncrementAndGetCounterValue` (lib/x86/libdatastore_shared_counter.so)
- `com.uptodown.util.NativeApiKey#getAuthApikey` (lib/x86/libuptodown-native.so)
- `com.uptodown.util.NativeApiKey#getAuthApikeyLite` (lib/x86/libuptodown-native.so)
- `com.uptodown.util.NativeApiKey#getAuthApikeyOpenAppStore` (lib/x86/libuptodown-native.so)
- `com.uptodown.util.NativeApiKey#getAuthApikeyDelta` (lib/x86/libuptodown-native.so)
- `com.uptodown.services.utils.NativeConst#getApiKeySeed` (lib/x86/libutd-services-native.so)
- `androidx.datastore.core.NativeSharedCounter#nativeTruncateFile` (lib/x86_64/libdatastore_shared_counter.so)
- `androidx.datastore.core.NativeSharedCounter#nativeCreateSharedCounter` (lib/x86_64/libdatastore_shared_counter.so)
- `androidx.datastore.core.NativeSharedCounter#nativeGetCounterValue` (lib/x86_64/libdatastore_shared_counter.so)
- `androidx.datastore.core.NativeSharedCounter#nativeIncrementAndGetCounterValue` (lib/x86_64/libdatastore_shared_counter.so)
- `com.uptodown.util.NativeApiKey#getAuthApikey` (lib/x86_64/libuptodown-native.so)
- `com.uptodown.util.NativeApiKey#getAuthApikeyLite` (lib/x86_64/libuptodown-native.so)
- `com.uptodown.util.NativeApiKey#getAuthApikeyOpenAppStore` (lib/x86_64/libuptodown-native.so)
- `com.uptodown.util.NativeApiKey#getAuthApikeyDelta` (lib/x86_64/libuptodown-native.so)
- `com.uptodown.services.utils.NativeConst#getApiKeySeed` (lib/x86_64/libutd-services-native.so)

## Imports (libc/outros) por lib

### lib/arm64-v8a/libandroidx.graphics.path.so

`__cxa_finalize`, `__cxa_atexit`, `__stack_chk_fail`, `__system_property_get`, `atoi`, `malloc`, `free`

### lib/arm64-v8a/libdatastore_shared_counter.so

`__cxa_finalize`, `__cxa_atexit`, `strerror`, `__stack_chk_fail`, `ftruncate`, `__errno`, `mmap`, `getauxval`, `__system_property_get`, `strncmp`

### lib/arm64-v8a/libuptodown-native.so

`__cxa_finalize`, `__cxa_atexit`, `__register_atfork`, `__stack_chk_fail`

### lib/arm64-v8a/libutd-services-native.so

`__cxa_finalize`, `__cxa_atexit`, `__stack_chk_fail`

### lib/armeabi-v7a/libandroidx.graphics.path.so

`__cxa_finalize`, `__cxa_atexit`, `__stack_chk_fail`, `__stack_chk_guard`, `__system_property_get`, `atoi`, `malloc`, `free`

### lib/armeabi-v7a/libdatastore_shared_counter.so

`__cxa_finalize`, `__cxa_atexit`, `strerror`, `__stack_chk_fail`, `__stack_chk_guard`, `ftruncate`, `__errno`, `mmap`

### lib/armeabi-v7a/libuptodown-native.so

`__cxa_finalize`, `__cxa_atexit`, `__register_atfork`, `__stack_chk_fail`, `__stack_chk_guard`

### lib/armeabi-v7a/libutd-services-native.so

`__cxa_finalize`, `__cxa_atexit`, `__stack_chk_fail`, `__stack_chk_guard`

### lib/x86/libandroidx.graphics.path.so

`__cxa_finalize`, `__cxa_atexit`, `__stack_chk_fail`, `__system_property_get`, `atoi`, `malloc`, `free`

### lib/x86/libdatastore_shared_counter.so

`__cxa_finalize`, `__cxa_atexit`, `strerror`, `__stack_chk_fail`, `ftruncate`, `__errno`, `mmap`

### lib/x86/libuptodown-native.so

`__cxa_finalize`, `__cxa_atexit`, `__register_atfork`, `__stack_chk_fail`

### lib/x86/libutd-services-native.so

`__cxa_finalize`, `__cxa_atexit`, `__stack_chk_fail`

### lib/x86_64/libandroidx.graphics.path.so

`__cxa_finalize`, `__cxa_atexit`, `__stack_chk_fail`, `__system_property_get`, `atoi`, `malloc`, `free`

### lib/x86_64/libdatastore_shared_counter.so

`__cxa_finalize`, `__cxa_atexit`, `strerror`, `__stack_chk_fail`, `ftruncate`, `__errno`, `mmap`

### lib/x86_64/libuptodown-native.so

`__cxa_finalize`, `__cxa_atexit`, `__register_atfork`, `__stack_chk_fail`

### lib/x86_64/libutd-services-native.so

`__cxa_finalize`, `__cxa_atexit`, `__stack_chk_fail`

> Disassembly amostral (400 instruções de `.text`) em `reports/native/*.disasm.txt`. Para decompilação de verdade use `ghidra/headless_run.sh`.
