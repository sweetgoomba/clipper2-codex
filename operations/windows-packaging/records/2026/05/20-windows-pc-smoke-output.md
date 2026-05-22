  # Windows PC Smoke Output - 2026-05-20

  ## PC / Path

  - ProjectRoot: C:\Users\bb\Desktop\project\clipper2
  - Windows version: 
    - OS Name: Microsoft Windows 11 Pro
    - OS Version: 10.0.26200 N/A Build 26200
  - Node: v22.12.0
  - npm: 11.0.0
  - Git: git version 2.47.0.windows.2
  - tar: bsdtar 3.8.4 - libarchive 3.8.4 zlib/1.2.13.1-motley liblzma/5.8.1 bz2lib/1.0.8 libzstd/1.5.7 cng/2.0 libb2/bundled 

  ## Guide Progress

  - Followed guide: /Users/jina/project/adlight/.codex/operations/windows-packaging/runbooks/windows-build-guide-configurable-root.md
  - Completed through step: ~12
  - Stopped at: 12

  ## Terminal Output

  ```text
PS C:\Users\bb\Desktop\project\clipper2> $ProjectRoot = (Get-Location).Path
PS C:\Users\bb\Desktop\project\clipper2> git --version
>> node -v
>> npm.cmd -v
>> tar --version
git version 2.47.0.windows.2
v22.12.0
11.0.0
bsdtar 3.8.4 - libarchive 3.8.4 zlib/1.2.13.1-motley liblzma/5.8.1 bz2lib/1.0.8 libzstd/1.5.7 cng/2.0 libb2/bundled 
PS C:\Users\bb\Desktop\project\clipper2> Write-Output $ProjectRoot
>> Get-Location
C:\Users\bb\Desktop\project\clipper2

Path                                
----                                
C:\Users\bb\Desktop\project\clipper2


PS C:\Users\bb\Desktop\project\clipper2> git clone https://github.com/OhMyMetabuzz/clipper_angular.git clipper_angular
>> git clone https://github.com/OhMyMetabuzz/clipper_electron.git clipper_electron
>> git clone https://github.com/OhMyMetabuzz/clipper_nestjs.git clipper_nestjs
>> git clone https://github.com/OhMyMetabuzz/clipper_python.git clipper_python
Cloning into 'clipper_angular'...
remote: Enumerating objects: 2761, done.
remote: Counting objects: 100% (2761/2761), done.
remote: Compressing objects: 100% (992/992), done.
remote: Total 2761 (delta 2007), reused 2472 (delta 1718), pack-reused 0 (from 0)
Receiving objects: 100% (2761/2761), 777.02 KiB | 10.50 MiB/s, done.
Resolving deltas: 100% (2007/2007), done.
Cloning into 'clipper_electron'...
remote: Enumerating objects: 350, done.
remote: Counting objects: 100% (350/350), done.
remote: Compressing objects: 100% (189/189), done.
remote: Total 350 (delta 187), reused 295 (delta 132), pack-reused 0 (from 0)
Receiving objects: 100% (350/350), 132.02 KiB | 4.26 MiB/s, done.
Resolving deltas: 100% (187/187), done.
Cloning into 'clipper_nestjs'...
remote: Enumerating objects: 1651, done.
remote: Counting objects: 100% (590/590), done.
remote: Compressing objects: 100% (197/197), done.
remote: Total 1651 (delta 450), reused 528 (delta 393), pack-reused 1061 (from 1)
Receiving objects: 100% (1651/1651), 54.06 MiB | 5.55 MiB/s, done.
Resolving deltas: 100% (1052/1052), done.
Cloning into 'clipper_python'...
remote: Enumerating objects: 1225, done.
remote: Counting objects: 100% (378/378), done.
remote: Compressing objects: 100% (167/167), done.
remote: Total 1225 (delta 236), reused 342 (delta 211), pack-reused 847 (from 1)
Receiving objects: 100% (1225/1225), 105.50 MiB | 10.89 MiB/s, done.
Resolving deltas: 100% (646/646), done.
PS C:\Users\bb\Desktop\project\clipper2> Get-ChildItem $ProjectRoot


    Directory: C:\Users\bb\Desktop\project\clipper2


Mode                 LastWriteTime         Length Name                                                                                                                        
----                 -------------         ------ ----                                                                                                                        
d-----        2026-05-20  오전 10:39                clipper_angular                                                                                                             
d-----        2026-05-20  오전 10:39                clipper_electron                                                                                                            
d-----        2026-05-20  오전 10:39                clipper_nestjs                                                                                                              
d-----        2026-05-20  오전 10:40                clipper_python                                                                                                              


PS C:\Users\bb\Desktop\project\clipper2> Set-Location (Join-Path $ProjectRoot 'clipper_angular')
>> git fetch
>> git checkout feature/initial-scaffold
>> git status --short --branch
>> git rev-parse --short HEAD
Already on 'feature/initial-scaffold'
Your branch is up to date with 'origin/feature/initial-scaffold'.
## feature/initial-scaffold...origin/feature/initial-scaffold
4501146
PS C:\Users\bb\Desktop\project\clipper2\clipper_angular> Set-Location (Join-Path $ProjectRoot 'clipper_electron')
>> git fetch
>> git checkout feature/windows-packaging
>> git status --short --branch
>> git rev-parse --short HEAD
branch 'feature/windows-packaging' set up to track 'origin/feature/windows-packaging'.
Switched to a new branch 'feature/windows-packaging'
## feature/windows-packaging...origin/feature/windows-packaging
e264865
PS C:\Users\bb\Desktop\project\clipper2\clipper_electron> Set-Location (Join-Path $ProjectRoot 'clipper_nestjs')
>> git fetch
>> git checkout feature/windows-packaging
>> git status --short --branch
>> git rev-parse --short HEAD
branch 'feature/windows-packaging' set up to track 'origin/feature/windows-packaging'.
Switched to a new branch 'feature/windows-packaging'
## feature/windows-packaging...origin/feature/windows-packaging
c33fbd8
PS C:\Users\bb\Desktop\project\clipper2\clipper_nestjs> Set-Location (Join-Path $ProjectRoot 'clipper_python')
>> git fetch
>> git checkout feature/windows-packaging
>> git status --short --branch
>> git rev-parse --short HEAD
branch 'feature/windows-packaging' set up to track 'origin/feature/windows-packaging'.
Switched to a new branch 'feature/windows-packaging'
## feature/windows-packaging...origin/feature/windows-packaging
5a61a62
PS C:\Users\bb\Desktop\project\clipper2\clipper_python> 



























                                                        $NestEnv = Join-Path $ProjectRoot 'clipper_nestjs\.env.local'
>> Write-Out^C          
PS C:\Users\bb\Desktop\project\clipper2\clipper_python> ^C
PS C:\Users\bb\Desktop\project\clipper2\clipper_python> ^C
PS C:\Users\bb\Desktop\project\clipper2\clipper_python> ^C
PS C:\Users\bb\Desktop\project\clipper2\clipper_python> $NestEnv = Join-Path $ProjectRoot 'clipper_nestjs\.env.local'
>> Write-Output $NestEnv
C:\Users\bb\Desktop\project\clipper2\clipper_nestjs\.env.local
PS C:\Users\bb\Desktop\project\clipper2\clipper_python> Get-Item $NestEnv | Select-Object FullName,Length,LastWriteTime

FullName                                                       Length LastWriteTime         
--------                                                       ------ -------------         
C:\Users\bb\Desktop\project\clipper2\clipper_nestjs\.env.local    425 2026-05-20 오전 10:42:23


PS C:\Users\bb\Desktop\project\clipper2\clipper_python> $NpmCache = Join-Path $ProjectRoot '.npm-cache'
>> Write-Output $NpmCache
C:\Users\bb\Desktop\project\clipper2\.npm-cache
PS C:\Users\bb\Desktop\project\clipper2\clipper_python> Set-Location (Join-Path $ProjectRoot 'clipper_angular')
>> npm.cmd install --cache $NpmCache
npm warn deprecated tar@6.2.1: Old versions of tar are not supported, and contain widely publicized security vulnerabilities, which have been fixed in the current version. Please update. Support for old versions may be purchased (at exorbitant rates) by contacting i@izs.me
npm warn deprecated rimraf@3.0.2: Rimraf versions prior to v4 are no longer supported
npm warn deprecated inflight@1.0.6: This module is not supported, and leaks memory. Do not use it. Check out lru-cache if you want a good and tested way to coalesce async requests by a key value, which is much more comprehensive and powerful.
npm warn deprecated glob@7.2.3: Old versions of glob are not supported, and contain widely publicized security vulnerabilities, which have been fixed in the current version. Please update. Support for old versions may be purchased (at exorbitant rates) by contacting i@izs.me
npm warn deprecated glob@10.5.0: Old versions of glob are not supported, and contain widely publicized security vulnerabilities, which have been fixed in the current version. Please update. Support for old versions may be purchased (at exorbitant rates) by contacting i@izs.me
npm warn deprecated glob@10.5.0: Old versions of glob are not supported, and contain widely publicized security vulnerabilities, which have been fixed in the current version. Please update. Support for old versions may be purchased (at exorbitant rates) by contacting i@izs.me

added 950 packages, and audited 951 packages in 11s

180 packages are looking for funding
  run `npm fund` for details

16 vulnerabilities (8 moderate, 8 high)

To address issues that do not require attention, run:
  npm audit fix

To address all issues (including breaking changes), run:
  npm audit fix --force

Run `npm audit` for details.
npm notice
npm notice New minor version of npm available! 11.0.0 -> 11.14.1
npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.14.1
npm notice To update run: npm install -g npm@11.14.1
npm notice
PS C:\Users\bb\Desktop\project\clipper2\clipper_angular> Set-Location (Join-Path $ProjectRoot 'clipper_nestjs')
>> npm.cmd install --cache $NpmCache
npm warn deprecated inflight@1.0.6: This module is not supported, and leaks memory. Do not use it. Check out lru-cache if you want a good and tested way to coalesce async requests by a key value, which is much more comprehensive and powerful.
npm warn deprecated glob@7.2.3: Old versions of glob are not supported, and contain widely publicized security vulnerabilities, which have been fixed in the current version. Please update. Support for old versions may be purchased (at exorbitant rates) by contacting i@izs.me
npm warn deprecated rimraf@2.7.1: Rimraf versions prior to v4 are no longer supported

added 293 packages, and audited 294 packages in 5s

42 packages are looking for funding
  run `npm fund` for details

8 vulnerabilities (5 moderate, 3 high)

To address issues that do not require attention, run:
  npm audit fix

To address all issues (including breaking changes), run:
  npm audit fix --force

Run `npm audit` for details.
PS C:\Users\bb\Desktop\project\clipper2\clipper_nestjs> Set-Location (Join-Path $ProjectRoot 'clipper_electron')
>> npm.cmd install --cache $NpmCache
npm warn deprecated inflight@1.0.6: This module is not supported, and leaks memory. Do not use it. Check out lru-cache if you want a good and tested way to coalesce async requests by a key value, which is much more comprehensive and powerful.
npm warn deprecated rimraf@3.0.2: Rimraf versions prior to v4 are no longer supported
npm warn deprecated glob@7.2.3: Old versions of glob are not supported, and contain widely publicized security vulnerabilities, which have been fixed in the current version. Please update. Support for old versions may be purchased (at exorbitant rates) by contacting i@izs.me
npm warn deprecated npmlog@6.0.2: This package is no longer supported.
npm warn deprecated are-we-there-yet@3.0.1: This package is no longer supported.
npm warn deprecated @npmcli/move-file@2.0.1: This functionality has been moved to @npmcli/fs
npm warn deprecated gauge@4.0.4: This package is no longer supported.
npm warn deprecated boolean@3.2.0: Package no longer supported. Contact Support at https://www.npmjs.com/support for more info.
npm warn deprecated tar@6.2.1: Old versions of tar are not supported, and contain widely publicized security vulnerabilities, which have been fixed in the current version. Please update. Support for old versions may be purchased (at exorbitant rates) by contacting i@izs.me
npm warn deprecated glob@8.1.0: Old versions of glob are not supported, and contain widely publicized security vulnerabilities, which have been fixed in the current version. Please update. Support for old versions may be purchased (at exorbitant rates) by contacting i@izs.me
npm warn deprecated glob@10.5.0: Old versions of glob are not supported, and contain widely publicized security vulnerabilities, which have been fixed in the current version. Please update. Support for old versions may be purchased (at exorbitant rates) by contacting i@izs.me

added 407 packages, and audited 408 packages in 10s

63 packages are looking for funding
  run `npm fund` for details

14 vulnerabilities (2 low, 2 moderate, 10 high)

To address issues that do not require attention, run:
  npm audit fix

To address all issues (including breaking changes), run:
  npm audit fix --force

Run `npm audit` for details.
PS C:\Users\bb\Desktop\project\clipper2\clipper_electron> Set-Location (Join-Path $ProjectRoot 'clipper_electron')
>> npm.cmd run fetch-uv

> clipper-electron@0.0.1 fetch-uv
> node scripts/fetch-uv.mjs

Downloading uv-darwin-arm64...
✓ uv-darwin-arm64
Downloading uv-darwin-x64...
✓ uv-darwin-x64
Downloading uv-win32-x64.exe...
✓ uv-win32-x64.exe

Done. Run "npm run fetch-uv" again only when upgrading uv.
npm notice
npm notice New minor version of npm available! 11.0.0 -> 11.14.1
npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.14.1
npm notice To update run: npm install -g npm@11.14.1
npm notice
PS C:\Users\bb\Desktop\project\clipper2\clipper_electron> Get-ChildItem (Join-Path $ProjectRoot 'clipper_electron\resources\bin')


    Directory: C:\Users\bb\Desktop\project\clipper2\clipper_electron\resources\bin


Mode                 LastWriteTime         Length Name                                                                                                                        
----                 -------------         ------ ----                                                                                                                        
-a----        2026-05-20  오전 10:39              0 .gitkeep                                                                                                                    
-a----        2025-12-16  오후 10:46       43486432 uv-darwin-arm64                                                                                                             
-a----        2025-12-16  오후 10:47       48659372 uv-darwin-x64                                                                                                               
-a----        2025-12-16   오후 1:52       62574080 uv-win32-x64.exe                                                                                                            


PS C:\Users\bb\Desktop\project\clipper2\clipper_electron> Set-Location (Join-Path $ProjectRoot 'clipper_electron')
>> node scripts\prepare-uv.mjs win32 x64
✓ uv-win32-x64.exe → uv.exe
PS C:\Users\bb\Desktop\project\clipper2\clipper_electron> Set-Location (Join-Path $ProjectRoot 'clipper_angular')
>> npm.cmd run build:electron -- --progress=false

> clipper-angular@0.0.0 build:electron
> ng build --configuration=electron --progress=false

Initial chunk files | Names                                       |  Raw size | Estimated transfer size
chunk-Y3MMG4T7.js   | -                                           | 143.52 kB |                42.39 kB
chunk-5QBUFFLH.js   | -                                           |  82.94 kB |                21.04 kB
chunk-WJGVALRI.js   | -                                           |  46.22 kB |                10.86 kB
chunk-QGP6FE42.js   | -                                           |  29.47 kB |                 6.45 kB
chunk-H6VCEVUY.js   | -                                           |  16.68 kB |                 4.97 kB
main-RFWMH3CC.js    | main                                        |  14.38 kB |                 4.07 kB
chunk-TLGNVK37.js   | -                                           |  11.19 kB |                 2.63 kB
chunk-IXCBMHRO.js   | -                                           |   8.17 kB |                 2.16 kB
chunk-OEMCMR7R.js   | -                                           |   6.38 kB |                 1.34 kB
styles-OLHFW2ES.css | styles                                      |   5.88 kB |                 1.36 kB
chunk-4MQPQZFJ.js   | -                                           |   4.77 kB |                 1.59 kB
chunk-Y57NZJEE.js   | -                                           |   4.45 kB |                 1.65 kB
chunk-BY4IGJBU.js   | -                                           |   4.12 kB |                 1.30 kB
chunk-7F2A7N6T.js   | -                                           | 582 bytes |               582 bytes
chunk-LY7OTYQB.js   | -                                           | 417 bytes |               417 bytes

                    | Initial total                               | 379.18 kB |               102.80 kB

Lazy chunk files    | Names                                       |  Raw size | Estimated transfer size
chunk-GS4USADD.js   | template-builder-page-component             | 271.22 kB |                52.89 kB
chunk-ILPG4664.js   | projects-component                          | 114.28 kB |                20.84 kB
chunk-YITRHATY.js   | browser                                     |  67.59 kB |                17.72 kB
chunk-ILRVV5DI.js   | clipper-studio-page-component               |  56.17 kB |                11.74 kB
chunk-G442GT2P.js   | dashboard-component                         |  26.15 kB |                 6.64 kB
chunk-552R33RC.js   | dialog-setup-component                      |  20.76 kB |                 5.62 kB
chunk-7HPJTBKM.js   | store-component                             |  15.37 kB |                 4.35 kB
chunk-4YAZ273I.js   | variation-page-component                    |  14.60 kB |                 3.72 kB
chunk-UPHEAMGN.js   | template-builder-redesign-preview-component |   8.80 kB |                 2.77 kB
chunk-4WWGIL65.js   | -                                           |   6.52 kB |                 2.08 kB
chunk-WXHRCYNC.js   | -                                           |   5.33 kB |               831 bytes
chunk-GZOPLXFT.js   | -                                           |   1.32 kB |               593 bytes
chunk-ZNPIQGU5.js   | dance-setup-component                       | 410 bytes |               410 bytes

Application bundle generation complete. [4.958 seconds]

Output location: C:\Users\bb\Desktop\project\clipper2\clipper_angular\dist\clipper_angular

PS C:\Users\bb\Desktop\project\clipper2\clipper_angular> Set-Location (Join-Path $ProjectRoot 'clipper_nestjs')
>> npm.cmd run bundle

> clipper-nestjs@0.0.1 bundle
> ncc build src/main.ts -o dist/bundled && node scripts/copy-assets.mjs dist/bundled

ncc: Version 0.38.4
ncc: Compiling file index.js into CJS
ncc: Using typescript@5.9.3 (local user-provided)
   3kB  dist\bundled\360.index.js
   6kB  dist\bundled\956.index.js
   9kB  dist\bundled\605.index.js
  15kB  dist\bundled\566.index.js
  25kB  dist\bundled\869.index.js
  31kB  dist\bundled\762.index.js
  32kB  dist\bundled\443.index.js
  45kB  dist\bundled\998.index.js
  51kB  dist\bundled\136.index.js
5864kB  dist\bundled\index.js
6081kB  [8332ms] - ncc 0.38.4
copied C:\Users\bb\Desktop\project\clipper2\clipper_nestjs\src\dance\data -> C:\Users\bb\Desktop\project\clipper2\clipper_nestjs\dist\bundled\dance\data
copied C:\Users\bb\Desktop\project\clipper2\clipper_nestjs\src\projects\assets -> C:\Users\bb\Desktop\project\clipper2\clipper_nestjs\dist\bundled\projects\assets
PS C:\Users\bb\Desktop\project\clipper2\clipper_nestjs> Set-Location (Join-Path $ProjectRoot 'clipper_electron')
>> npm.cmd run build

> clipper-electron@0.0.1 build
> tsc -p tsconfig.json

PS C:\Users\bb\Desktop\project\clipper2\clipper_electron> Set-Location (Join-Path $ProjectRoot 'clipper_electron')
>> node scripts\prepare-uv.mjs win32 x64
✓ uv-win32-x64.exe → uv.exe
PS C:\Users\bb\Desktop\project\clipper2\clipper_electron> Set-Location (Join-Path $ProjectRoot 'clipper_electron')
>> npm.cmd run build:app:win:x64

> clipper-electron@0.0.1 build:app:win:x64
> node scripts/build-app.mjs win32 x64


=== ClipperStudio [win32/x64] ===

── Step 0/5: Clean Python bytecode cache
── Step 1/5: Angular build

> npm run build:electron -- --progress=false

> clipper-angular@0.0.0 build:electron
> ng build --configuration=electron --progress=false

Initial chunk files | Names                                       |  Raw size | Estimated transfer size
chunk-Y3MMG4T7.js   | -                                           | 143.52 kB |                42.39 kB
chunk-5QBUFFLH.js   | -                                           |  82.94 kB |                21.04 kB
chunk-WJGVALRI.js   | -                                           |  46.22 kB |                10.86 kB
chunk-QGP6FE42.js   | -                                           |  29.47 kB |                 6.45 kB
chunk-H6VCEVUY.js   | -                                           |  16.68 kB |                 4.97 kB
main-RFWMH3CC.js    | main                                        |  14.38 kB |                 4.07 kB
chunk-TLGNVK37.js   | -                                           |  11.19 kB |                 2.63 kB
chunk-IXCBMHRO.js   | -                                           |   8.17 kB |                 2.16 kB
chunk-OEMCMR7R.js   | -                                           |   6.38 kB |                 1.34 kB
styles-OLHFW2ES.css | styles                                      |   5.88 kB |                 1.36 kB
chunk-4MQPQZFJ.js   | -                                           |   4.77 kB |                 1.59 kB
chunk-Y57NZJEE.js   | -                                           |   4.45 kB |                 1.65 kB
chunk-BY4IGJBU.js   | -                                           |   4.12 kB |                 1.30 kB
chunk-7F2A7N6T.js   | -                                           | 582 bytes |               582 bytes
chunk-LY7OTYQB.js   | -                                           | 417 bytes |               417 bytes

                    | Initial total                               | 379.18 kB |               102.80 kB

Lazy chunk files    | Names                                       |  Raw size | Estimated transfer size
chunk-GS4USADD.js   | template-builder-page-component             | 271.22 kB |                52.89 kB
chunk-ILPG4664.js   | projects-component                          | 114.28 kB |                20.84 kB
chunk-YITRHATY.js   | browser                                     |  67.59 kB |                17.72 kB
chunk-ILRVV5DI.js   | clipper-studio-page-component               |  56.17 kB |                11.74 kB
chunk-G442GT2P.js   | dashboard-component                         |  26.15 kB |                 6.64 kB
chunk-552R33RC.js   | dialog-setup-component                      |  20.76 kB |                 5.62 kB
chunk-7HPJTBKM.js   | store-component                             |  15.37 kB |                 4.35 kB
chunk-4YAZ273I.js   | variation-page-component                    |  14.60 kB |                 3.72 kB
chunk-UPHEAMGN.js   | template-builder-redesign-preview-component |   8.80 kB |                 2.77 kB
chunk-4WWGIL65.js   | -                                           |   6.52 kB |                 2.08 kB
chunk-WXHRCYNC.js   | -                                           |   5.33 kB |               831 bytes
chunk-GZOPLXFT.js   | -                                           |   1.32 kB |               593 bytes
chunk-ZNPIQGU5.js   | dance-setup-component                       | 410 bytes |               410 bytes

Application bundle generation complete. [2.844 seconds]

Output location: C:\Users\bb\Desktop\project\clipper2\clipper_angular\dist\clipper_angular


── Step 2/5: NestJS bundle

> npm run bundle

> clipper-nestjs@0.0.1 bundle
> ncc build src/main.ts -o dist/bundled && node scripts/copy-assets.mjs dist/bundled

ncc: Version 0.38.4
ncc: Compiling file index.js into CJS
ncc: Using typescript@5.9.3 (local user-provided)
   3kB  dist\bundled\360.index.js
   6kB  dist\bundled\956.index.js
   9kB  dist\bundled\605.index.js
  15kB  dist\bundled\566.index.js
  25kB  dist\bundled\869.index.js
  31kB  dist\bundled\762.index.js
  32kB  dist\bundled\443.index.js
  45kB  dist\bundled\998.index.js
  51kB  dist\bundled\136.index.js
5864kB  dist\bundled\index.js
6081kB  [5309ms] - ncc 0.38.4
copied C:\Users\bb\Desktop\project\clipper2\clipper_nestjs\src\dance\data -> C:\Users\bb\Desktop\project\clipper2\clipper_nestjs\dist\bundled\dance\data
copied C:\Users\bb\Desktop\project\clipper2\clipper_nestjs\src\projects\assets -> C:\Users\bb\Desktop\project\clipper2\clipper_nestjs\dist\bundled\projects\assets

── Step 3/5: Electron TypeScript compile

> npx tsc -p tsconfig.json

── Step 4/5: Prepare uv binary

> node scripts/prepare-uv.mjs win32 x64
✓ uv-win32-x64.exe → uv.exe

── Step 5/5: electron-builder

> npx electron-builder --win --x64
  • electron-builder  version=25.1.8 os=10.0.26200
  • loaded configuration  file=C:\Users\bb\Desktop\project\clipper2\clipper_electron\electron-builder.yml
  • author is missed in the package.json  appPackageFile=C:\Users\bb\Desktop\project\clipper2\clipper_electron\package.json
  • writing effective config  file=dist-app\builder-effective-config.yaml
  • executing @electron/rebuild  electronVersion=33.4.11 arch=x64 buildFromSource=false appDir=./
  • installing native dependencies  arch=x64
  • completed installing native dependencies
  • packaging       platform=win32 arch=x64 electron=33.4.11 appOutDir=dist-app\win-unpacked
  • updating asar integrity executable resource  executablePath=dist-app\win-unpacked\Clipper2.exe
  • default Electron icon is used  reason=application icon is not set
  • signing with signtool.exe  path=dist-app\win-unpacked\Clipper2.exe
  • no signing info identified, signing is skipped  signHook=false cscInfo=null
  • building        target=nsis file=dist-app\Clipper2 Setup 0.0.1.exe archs=x64 oneClick=false perMachine=false
  • signing with signtool.exe  path=dist-app\win-unpacked\resources\elevate.exe
  • no signing info identified, signing is skipped  signHook=false cscInfo=null
  • signing with signtool.exe  path=dist-app\__uninstaller-nsis-clipper-electron.exe
  • no signing info identified, signing is skipped  signHook=false cscInfo=null
  • signing with signtool.exe  path=dist-app\Clipper2 Setup 0.0.1.exe
  • no signing info identified, signing is skipped  signHook=false cscInfo=null
  • building block map  blockMapFile=dist-app\Clipper2 Setup 0.0.1.exe.blockmap

✓ Done. Artifacts in dist-app/
PS C:\Users\bb\Desktop\project\clipper2\clipper_electron> $ElectronRoot = Join-Path $ProjectRoot 'clipper_electron'
>> Set-Location $ElectronRoot
>> Get-ChildItem .\dist-app


    Directory: C:\Users\bb\Desktop\project\clipper2\clipper_electron\dist-app


Mode                 LastWriteTime         Length Name                                                                                                                        
----                 -------------         ------ ----                                                                                                                        
d-----        2026-05-20  오전 10:47                win-unpacked                                                                                                                
-a----        2026-05-20  오전 10:48           7242 builder-debug.yml                                                                                                           
-a----        2026-05-20  오전 10:47           1397 builder-effective-config.yaml                                                                                               
-a----        2026-05-20  오전 10:48      165487013 Clipper2 Setup 0.0.1.exe                                                                                                    
-a----        2026-05-20  오전 10:48         172561 Clipper2 Setup 0.0.1.exe.blockmap                                                                                           
-a----        2026-05-20  오전 10:48            345 latest.yml                                                                                                                  


PS C:\Users\bb\Desktop\project\clipper2\clipper_electron> Get-Item '.\dist-app\Clipper2 Setup 0.0.1.exe' | Select-Object FullName,Length,LastWriteTime

FullName                                                                                   Length LastWriteTime         
--------                                                                                   ------ -------------         
C:\Users\bb\Desktop\project\clipper2\clipper_electron\dist-app\Clipper2 Setup 0.0.1.exe 165487013 2026-05-20 오전 10:48:06


PS C:\Users\bb\Desktop\project\clipper2\clipper_electron> Test-Path '.\dist-app\win-unpacked\resources\bin\uv.exe'
>> Test-Path '.\dist-app\win-unpacked\resources\clipper_nestjs\.env.local'
True
True
PS C:\Users\bb\Desktop\project\clipper2\clipper_electron> $Installer = Join-Path $ProjectRoot 'clipper_electron\dist-app\Clipper2 Setup 0.0.1.exe'
>> Write-Output $Installer
C:\Users\bb\Desktop\project\clipper2\clipper_electron\dist-app\Clipper2 Setup 0.0.1.exe
PS C:\Users\bb\Desktop\project\clipper2\clipper_electron> $InstallDir = Join-Path $ProjectRoot 'clipper2-smoke-install'
>> Write-Output $InstallDir
C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install
PS C:\Users\bb\Desktop\project\clipper2\clipper_electron> Test-Path (Join-Path $InstallDir 'Clipper2.exe')
False
PS C:\Users\bb\Desktop\project\clipper2\clipper_electron> Test-Path (Join-Path $InstallDir 'Clipper2.exe')
False
PS C:\Users\bb\Desktop\project\clipper2\clipper_electron> Test-Path (Join-Path $InstallDir 'Clipper2.exe')
False
PS C:\Users\bb\Desktop\project\clipper2\clipper_electron> $Installer = Join-Path $ProjectRoot 'clipper_electron\dist-app\Clipper2 Setup 0.0.1.exe'
PS C:\Users\bb\Desktop\project\clipper2\clipper_electron> $InstallDir = Join-Path $ProjectRoot 'clipper2-smoke-install'
>> Start-Process -FilePath $Installer -ArgumentList "/S /D=$InstallDir" -Wait
PS C:\Users\bb\Desktop\project\clipper2\clipper_electron> Test-Path (Join-Path $InstallDir 'Clipper2.exe')
>> Get-ChildItem $InstallDir
True


    Directory: C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install


Mode                 LastWriteTime         Length Name                                                                                                                        
----                 -------------         ------ ----                                                                                                                        
d-----        2026-05-20  오전 10:50                locales                                                                                                                     
d-----        2026-05-20  오전 10:50                resources                                                                                                                   
-a----        2026-05-20  오전 10:48         151599 chrome_100_percent.pak                                                                                                      
-a----        2026-05-20  오전 10:48         228644 chrome_200_percent.pak                                                                                                      
-a----        2026-05-20  오전 10:48      188784128 Clipper2.exe                                                                                                                
-a----        2026-05-20  오전 10:48        4916728 d3dcompiler_47.dll                                                                                                          
-a----        2026-05-20  오전 10:48        2927616 ffmpeg.dll                                                                                                                  
-a----        2026-05-20  오전 10:48       10468208 icudtl.dat                                                                                                                  
-a----        2026-05-20  오전 10:48         493056 libEGL.dll                                                                                                                  
-a----        2026-05-20  오전 10:48        8417792 libGLESv2.dll                                                                                                               
-a----        2026-05-20  오전 10:48           1096 LICENSE.electron.txt                                                                                                        
-a----        2026-05-20  오전 10:48        9170910 LICENSES.chromium.html                                                                                                      
-a----        2026-05-20  오전 10:48        5756465 resources.pak                                                                                                               
-a----        2026-05-20  오전 10:48         316538 snapshot_blob.bin                                                                                                           
-a----        2026-05-20  오전 10:48         170155 Uninstall Clipper2.exe                                                                                                      
-a----        2026-05-20  오전 10:48         687473 v8_context_snapshot.bin                                                                                                     
-a----        2026-05-20  오전 10:48        5533184 vk_swiftshader.dll                                                                                                          
-a----        2026-05-20  오전 10:48            106 vk_swiftshader_icd.json                                                                                                     
-a----        2026-05-20  오전 10:48         894976 vulkan-1.dll                                                                                                                


PS C:\Users\bb\Desktop\project\clipper2\clipper_electron> $InstallDir = Join-Path $ProjectRoot 'clipper2-smoke-install'
>> $ClipperExe = Join-Path $InstallDir 'Clipper2.exe'
>> Start-Process $ClipperExe
PS C:\Users\bb\Desktop\project\clipper2\clipper_electron> 
[logger] main log → C:\Users\bb\AppData\Roaming\Clipper2\logs\main.log
[setup] Syncing Python env → C:\Users\bb\AppData\Roaming\Clipper2\clipper_venv
[setup] First launch may take several minutes (downloading Python + packages).
[uv sync] Using CPython 3.11.9 interpreter at: C:\Users\bb\AppData\Local\Programs\Python\Python311\python.exe
[uv sync] Creating virtual environment at: C:\Users\bb\AppData\Roaming\Clipper2\clipper_venv
[uv sync] Resolved 142 packages in 2ms
[uv sync]    Building clipper-plugin-dialog-highlight @ file:///C:/Users/bb/Desktop/project/clipper2/clipper2-smoke-install/resources/clipper_python/plugins/dialog_highlight
[uv sync]    Building clipper-plugin-sdk @ file:///C:/Users/bb/Desktop/project/clipper2/clipper2-smoke-install/resources/clipper_python/clipper_plugin_sdk
[uv sync]    Building clipper-plugin-dance-highlight @ file:///C:/Users/bb/Desktop/project/clipper2/clipper2-smoke-install/resources/clipper_python/plugins/dance_highlight
[uv sync]    Building clipper-plugin-clipper1-video-render @ file:///C:/Users/bb/Desktop/project/clipper2/clipper2-smoke-install/resources/clipper_python/plugins/clipper1_video_render
[uv sync] Downloading networkx (2.0MiB)
[uv sync] Downloading setuptools (1.0MiB)
[uv sync] Downloading openai (1.1MiB)
[uv sync] 
[uv sync] Downloading av (27.6MiB)
[uv sync] Downloading pillow (6.8MiB)
[uv sync] 
[uv sync] Downloading fonttools
[uv sync] (2.2MiB)
[uv sync] Downloading pygments (1.2MiB)
[uv sync] Downloading scikit-learn (7.7MiB)
[uv sync] Downloading yt-dlp (3.2MiB)
[uv sync] Downloading sympy (6.0MiB)
[uv sync] Downloading tokenizers (2.6MiB)
[uv sync] 
[uv sync] Downloading opencv-python-headless (38.2MiB)
[uv sync] Downloading matplotlib (7.8MiB)
[uv sync] Downloading polars-runtime-32 (44.8MiB)
[uv sync] Downloading hf-xet (3.5MiB)
[uv sync] Downloading llvmlite (36.4MiB)
[uv sync] Downloading cython (2.6MiB)
[uv sync] Downloading timm (2.4MiB)
[uv sync] Downloading scipy (34.9MiB)
[uv sync] Downloading faster-whisper (1.1MiB)
[uv sync] 
[uv sync] Downloading ultralytics (1.2MiB)
[uv sync] Downloading onnx (15.7MiB)
[uv sync] Downloading numba (2.6MiB)
[uv sync] 
[uv sync] Downloading ctranslate2 (18.0MiB)
[uv sync] Downloading pydantic-core (2.0MiB)
[uv sync] Downloading opencv-python (38.3MiB)
[uv sync] Downloading torchvision
[uv sync]  (3.8MiB)
[uv sync] Downloading open-clip-torch (1.5MiB)
[uv sync] Downloading onnxruntime (12.0MiB)
[uv sync] Downloading scikit-image (11.3MiB)
[uv sync] 
[uv sync] Downloading uharfbuzz (1.3MiB)
[uv sync] Downloading numpy (12.0MiB)
[uv sync] Downloading torch (109.2MiB)
[uv sync]    Building insightface==0.7.3
[uv sync]       Built clipper-plugin-dance-highlight @ file:///C:/Users/bb/Desktop/project/clipper2/clipper2-smoke-install/resources/clipper_python/plugins/dance_highlight
[uv sync]       Built clipper-plugin-clipper1-video-render @ file:///C:/Users/bb/Desktop/project/clipper2/clipper2-smoke-install/resources/clipper_python/plugins/clipper1_video_render
[uv sync]       Built clipper-plugin-dialog-highlight @ file:///C:/Users/bb/Desktop/project/clipper2/clipper2-smoke-install/resources/clipper_python/plugins/dialog_highlight
[uv sync]       Built clipper-plugin-sdk @ file:///C:/Users/bb/Desktop/project/clipper2/clipper2-smoke-install/resources/clipper_python/clipper_plugin_sdk
[uv sync]  Downloaded faster-whisper
[uv sync]  Downloaded uharfbuzz
[uv sync]  Downloaded ultralytics
[uv sync]  Downloaded pygments
[uv sync]  Downloaded setuptools
[uv sync]  Downloaded pydantic-core
[uv sync]  Downloaded open-clip-torch
[uv sync]  Downloaded fonttools
[uv sync]  Downloaded tokenizers
[uv sync]  Downloaded networkx
[uv sync]  Downloaded timm
[uv sync]  Downloaded cython
[uv sync]  Downloaded numba
[uv sync]  Downloaded hf-xet
[uv sync]  Downloaded torchvision
[uv sync]  Downloaded openai
[uv sync]  Downloaded yt-dlp
[uv sync]  Downloaded sympy
[uv sync]  Downloaded pillow
[uv sync]  Downloaded scikit-learn
[uv sync]  Downloaded matplotlib
[uv sync]  Downloaded scikit-image
[uv sync]  Downloaded onnxruntime
[uv sync]  Downloaded numpy
[uv sync]  Downloaded onnx
[uv sync]  Downloaded ctranslate2
[uv sync]  Downloaded av
[uv sync]       Built insightface==0.7.3
[uv sync]  Downloaded scipy
[uv sync]  Downloaded llvmlite
[uv sync]  Downloaded opencv-python-headless
[uv sync]  Downloaded opencv-python
[uv sync]  Downloaded polars-runtime-32
[uv sync]  Downloaded torch
[uv sync] Prepared 116 packages in 48.16s
[uv sync] Installed 116 packages in 6.07s
[uv sync]  + albucore==0.0.24
 + albumentations==2.0.8
 +
[uv sync]  annotated-doc==0.0.4
 + annotated-types==0.7.0
 + anyio==4.13.0
 + audioread==
[uv sync] 3.1.0
 + av==17.0.0
 + certifi==2026.2.25
 + cffi
[uv sync] ==2.0.0
 + charset-normalizer==3.4.7
 + click==8.2.1
 +
[uv sync] clipper-plugin-clipper1-video-render==0.1.0 (from file:///C:/Users/bb/Desktop/project/clipper2/clipper2-smoke-install/resources/clipper_python/plugins/clipper1_video_render)
 + clipper-plugin-dance-highlight==0.1.0 (from file:///C:/Users/bb/Desktop/project/clipper2/clipper2-smoke-install/resources/clipper_python/plugins/dance_highlight)
 +
[uv sync] clipper-plugin-dialog-highlight==0.1.0 (from file:///C:/Users/bb/Desktop/project/clipper2/clipper2-smoke-install/resources/clipper_python/plugins/dialog_highlight)
 + clipper-plugin-sdk==0.1.0 (from file:///C:/Users/bb/Desktop/project/clipper2/clipper2-smoke-install/resources/clipper_python/clipper_plugin_sdk)
 + colorama==0.4
[uv sync] .6
 + contourpy==1.3.3
 + ctranslate2==4.7.1
 +
[uv sync] cycler==0.12.1
 + cython==3.2.4
 + decorator==5.2.
[uv sync] 1
 + distro==1.9.0
 + easydict==1.13
 + fastapi==0.
[uv sync] 136.0
 + faster-whisper==1.2.1
 + filelock==3.28.0
[uv sync] + flatbuffers==25.12.19
 + fonttools==4.62.1
 + fsspec
[uv sync] ==2026.3.0
 + ftfy==6.3.1
 + h11==0.16.0
[uv sync] 
 + hf-xet==1.4.3
 + httpcore==1.0.9
 +
[uv sync] httptools==0.7.1
 + httpx==0.28.1
 + huggingface-hub==
[uv sync] 1.11.0
 + idna==3.11
 +
[uv sync] imageio==2.37.3
 + insightface==0.7.3
[uv sync]  + jinja2==3.1.6
 + jiter==0.14.0
 +
[uv sync]  joblib==1.5.3
 + kiwisolver==1.5.0
 + lazy-loader==
[uv sync] 0.5
 + librosa==0.11.0
 + llvmlite==
[uv sync] 0.47.0
 + markdown-it-py==4.0.0
 + markupsafe==
[uv sync] 3.0.3
 + matplotlib==3.10.8
 + mdurl==
[uv sync] 0.1.2
 + ml-dtypes==0.5.4
 + mpmath==
[uv sync] 1.3.0
 + msgpack==1.1.2
 +
[uv sync] networkx==3.6.1
 + numba==0.65.0
 +
[uv sync]  numpy==2.4.4
 + onnx==1.21.0
 +
[uv sync]  onnxruntime==1.24.4
 + open-clip-torch==3.3.0
 +
[uv sync]  openai==2.32.0
 + opencv-python==4.13.0.92
 +
[uv sync]  opencv-python-headless==4.13.0.92
 + packaging==26.1
[uv sync]  + pillow==12.2.0
 + platformdirs==4.
[uv sync] 9.6
 + polars==1.39.3
 + polars-runtime-32==1.39
[uv sync] .3
 + pooch==1.9.0
 +
[uv sync]  prettytable==3.17.0
 + protobuf==7.34.1
 + psutil
[uv sync] ==7.2.2
 + pycparser==3.0
 + pydantic==2.13.1
 +
[uv sync]  pydantic-core==2.46.1
 + pygments==2.20.0
 + pyparsing==3.3.2
[uv sync] + python-dateutil==2.9.0.post0
 + python-dotenv==1.2.2
 + pyyaml==6.0.3
[uv sync] + regex==2026.4.4
 + requests==2.33.1
 + rich==15.0.
[uv sync] 0
 + safetensors==0.7.0
 + scenedetect==0.6.7.1
[uv sync] + scikit-image==0.26.0
 + scikit-learn==1.8.0
 +
[uv sync] scipy==1.17.1
 + setuptools==81.0.0
 + shellingham
[uv sync] ==1.5.4
 + simsimd==6.5.16
 + six
[uv sync] ==1.17.0
 + sniffio==1.3.1
 + soundfile==0.13.1
[uv sync] + soxr==1.0.0
 + starlette==1.0.0
 + stringzilla==4.6.0
[uv sync] 
 + sympy==1.14.0
 + threadpoolctl==3.6.0
 +
[uv sync]  tifffile==2026.3.3
 + timm==1.0.26
 + tokenizers==0
[uv sync] .22.2
 + torch==2.11.0
 + torchvision==0.26.0
[uv sync] 
 + tqdm==4.67.3
 + typer==0.24.1
 +
[uv sync]  typing-extensions==4.15.0
 + typing-inspection==0.4.2
 + uharfbuzz==
[uv sync] 0.54.1
 + ultralytics==8.4.38
 + ultralytics-thop==2.0.18
[uv sync]  + urllib3==2.6.3
 + uvicorn==0.44.0
[uv sync] + watchfiles==1.1.1
 + wcwidth==0.6.0
 +
[uv sync] websockets==16.0
 + yt-dlp==2026.3.17
[setup] Python env ready.
[PluginHostBridge] listening on http://127.0.0.1:52264
[window] showing main window
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:28     LOG [NestFactory] Starting Nest application...
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [ArtistDetectorService] loaded 7468 artists, 10376 search entries
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [InstanceLoader] ExecutionModule dependencies initialized +1ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [InstanceLoader] AppModule dependencies initialized +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [InstanceLoader] ConfigHostModule dependencies initialized +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [InstanceLoader] ResourcesModule dependencies initialized +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [InstanceLoader] ConfigModule dependencies initialized +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [InstanceLoader] AuthModule dependencies initialized +23ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [InstanceLoader] SourcesModule dependencies initialized +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [InstanceLoader] DanceModule dependencies initialized +1ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [InstanceLoader] EventsModule dependencies initialized +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [InstanceLoader] PluginsModule dependencies initialized +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [InstanceLoader] ProjectManifestModule dependencies initialized +1ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [InstanceLoader] TemplateBuilderModule dependencies initialized +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [InstanceLoader] JobsModule dependencies initialized +1ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [InstanceLoader] ProjectsModule dependencies initialized +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RoutesResolver] HealthController {/v1/health}: +2ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/health, GET} route +1ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RoutesResolver] DanceController {/v1/dance}: +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/dance/artists/detect, POST} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/dance/artists/members, POST} route +1ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/dance/members/images, POST} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/dance/members/images/more, POST} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RoutesResolver] PluginsController {/v1/plugins}: +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/plugins, GET} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/plugins/:name, GET} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/plugins/:name/status, GET} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/plugins/:name/resource-assessment, GET} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/plugins/:name/runtime-accelerators, GET} route +1ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/plugins/:name/start, POST} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/plugins/:name/stop, POST} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RoutesResolver] ResourcesController {/v1/resources}: +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/resources, GET} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RoutesResolver] SourcesController {/v1/sources}: +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/sources/inspect, POST} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/sources/ingest, POST} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/sources/file, GET} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RoutesResolver] TemplatePresetsController {/v1/template-presets}: +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-presets, GET} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-presets/legacy-clipper1/assets/:fileName, GET} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-presets/:presetId, GET} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RoutesResolver] TemplateBuilderController {/v1/template-builder}: +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-builder/families, GET} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-builder/families/:familyId, GET} route +1ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-builder/admin/system-template-edit-mode, POST} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-builder/families, POST} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-builder/families/:familyId, PATCH} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-builder/families/:familyId/common-styles/:role, PATCH} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-builder/families/:familyId, DELETE} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-builder/families/:familyId/clone, POST} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-builder/families/:familyId/variants/:ratio, POST} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-builder/families/:familyId/variants/:ratio, PATCH} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-builder/families/:familyId/variants/:ratio/validate, POST} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-builder/families/:familyId/variants/:ratio/sample-render, POST} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-builder/families/:familyId/variants/:ratio/preview/text-artifacts/:layerId, POST} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-builder/preview/renderer-session, POST} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-builder/families/:familyId/variants/:ratio/preview/subtitle-artifact, POST} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-builder/families/:familyId/variants/:ratio/sample-render/file, GET} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-builder/families/:familyId/variants/:ratio/sample-render/thumbnail/file, GET} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-builder/families/:familyId/variants/:ratio/assets/layout-image/file, GET} route +1ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-builder/assets/file, GET} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-builder/families/:familyId/variants/:ratio/assets/layout-image, POST} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-builder/families/:familyId/card-thumbnail, POST} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-builder/families/:familyId/variants/:ratio/assets/layout-layers/:layoutLayerId/file, GET} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-builder/families/:familyId/variants/:ratio/assets/layout-layers/:layoutLayerId, POST} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-builder/families/:familyId/variants/:ratio/assets/logo-image/file, GET} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-builder/families/:familyId/variants/:ratio/assets/fonts/:layerId/file, GET} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-builder/families/:familyId/variants/:ratio/assets/logo-image, POST} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-builder/families/:familyId/variants/:ratio/assets/fonts/:layerId, POST} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/template-builder/families/:familyId/register-official, POST} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RoutesResolver] ProjectsController {/v1/projects}: +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects, GET} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/clipper-studio/tts-presets, GET} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/clipper-studio/capabilities, GET} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/clipper-studio, POST} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/:projectId/clipper-studio/draft, POST} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/:projectId/clipper-studio/draft-jobs, POST} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/:projectId/clipper-studio/draft-jobs, GET} route +1ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/:projectId/clipper-studio/draft-jobs/:draftJobId, GET} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/:projectId/clipper-studio/draft-jobs/:draftJobId, DELETE} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/:projectId/clipper-studio/edit-state, PATCH} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/:projectId/clipper-studio/media, POST} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/:projectId/clipper-studio/media/search, POST} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/:projectId/clipper-studio/media/remote, POST} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/:projectId/clipper-studio/media/generate, POST} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/:projectId/clipper-studio/media/search-import, POST} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/by-job/:jobId, GET} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/:projectId/detail, GET} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/:projectId/manifest, GET} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/:projectId/outputs/:outputId/render-recipe, GET} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/:projectId/outputs/:outputId/render-providers, GET} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/:projectId/outputs/:outputId/render-jobs, POST} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/:projectId/render-jobs, GET} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/:projectId/render-jobs/:renderJobId, GET} route +1ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/:projectId/render-jobs/:renderJobId, DELETE} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/:projectId/file, GET} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/:projectId, GET} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RoutesResolver] Clipper1WorkspaceController {/v1/projects/clipper1/workspaces}: +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/clipper1/workspaces, GET} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/clipper1/workspaces, POST} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/clipper1/workspaces/:workspaceId, GET} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/clipper1/workspaces/:workspaceId, PATCH} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/clipper1/workspaces/:workspaceId/clips, POST} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/clipper1/workspaces/:workspaceId/clips/:clipId/media/search, POST} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/clipper1/workspaces/:workspaceId/clips/:clipId/media/remote, POST} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/clipper1/workspaces/:workspaceId/clips/:clipId/media/local, POST} route +1ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/clipper1/workspaces/:workspaceId/clips/:clipId/media/source-path, POST} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/clipper1/workspaces/:workspaceId/clips/:clipId/media/reuse, POST} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/clipper1/workspaces/:workspaceId/clips/:clipId/media/:assetId/remote, PUT} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/clipper1/workspaces/:workspaceId/clips/:clipId/media/:assetId/local, PUT} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/clipper1/workspaces/:workspaceId/clips/:clipId/media/:assetId/source-path, PUT} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/clipper1/workspaces/:workspaceId/clips/:clipId/media/slots, PATCH} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/clipper1/workspaces/:workspaceId/clips/:clipId/media/order, PATCH} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/clipper1/workspaces/:workspaceId/clips/:clipId/media/:assetId, DELETE} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/clipper1/workspaces/:workspaceId/clips/:clipId/media/search-import, POST} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/clipper1/workspaces/:workspaceId/render-jobs, POST} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RoutesResolver] VariationWorkspaceController {/v1/projects/variation/workspaces}: +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/variation/workspaces, GET} route +1ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/variation/workspaces, POST} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/variation/workspaces/:workspaceId, GET} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/projects/variation/workspaces/:workspaceId, PATCH} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RoutesResolver] JobsController {/v1/jobs}: +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/jobs, POST} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/jobs, GET} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/jobs/:jobId, GET} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/jobs/:jobId, DELETE} route +0ms
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/jobs/:jobId/reorder, POST} route +0ms
[Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [RouterExplorer] Mapped {/v1/jobs/:jobId/retry, POST} route +0ms
[nestjs] (node:6940) Warning: NodeVersionSupportWarning: The AWS SDK for JavaScript (v3)
versions published after the first week of January 2027
will require node >=22. You are running node v20.18.3.

To continue receiving updates to AWS services, bug fixes,
and security updates please upgrade to node >=22.

More information can be found at: https://a.co/c895JFp
(Use `Clipper2 --trace-warnings ...` to show where the warning was created)
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 10:51:29     LOG [NestApplication] Nest application successfully started +4ms
[nestjs] [clipper-nestjs] listening on http://127.0.0.1:52267
[NestManager] ready at http://127.0.0.1:52267/v1

... (앱에서 ffmpeg,ffprobe 설치 시도, ui에 보인 에러메세지: 
다운로드 실패
Error: Error invoking remote method 'clipper:download:startFfmpeg': Error: HTTP 404 for https://registry.npmjs.org/@ffprobe-installer/win32-x64/-/win32-x64-5.0.1.tgz)
...

    at async C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:29799:17
[ffmpeg] Downloading ffprobe for win32-x64…
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 11:01:36   ERROR [ExceptionsHandler] Plugin 'electron-bridge' is unavailable: HTTP 404 for https://registry.npmjs.org/@ffprobe-installer/win32-x64/-/win32-x64-5.0.1.tgz
PluginHostUnavailableError: Plugin 'electron-bridge' is unavailable: HTTP 404 for https://registry.npmjs.org/@ffprobe-installer/win32-x64/-/win32-x64-5.0.1.tgz
    at ElectronPluginHost.parseResponse (C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:114995:15)
    at process.processTicksAndRejections (node:internal/process/task_queues:95:5)
    at async ElectronPluginHost.ensureStarted (C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:114954:21)
    at async TemplateBuilderTextArtifactWorkerClient.renderTextArtifact (C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:131047:25)
    at async TemplateBuilderTextArtifactService.render (C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:131206:20)
    at async C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:29334:28
    at async C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:29799:17
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 11:01:36   ERROR [ExceptionsHandler] Plugin 'electron-bridge' is unavailable: HTTP 404 for https://registry.npmjs.org/@ffprobe-installer/win32-x64/-/win32-x64-5.0.1.tgz
PluginHostUnavailableError: Plugin 'electron-bridge' is unavailable: HTTP 404 for https://registry.npmjs.org/@ffprobe-installer/win32-x64/-/win32-x64-5.0.1.tgz
    at ElectronPluginHost.parseResponse (C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:114995:15)
    at process.processTicksAndRejections (node:internal/process/task_queues:95:5)
    at async ElectronPluginHost.ensureStarted (C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:114954:21)
    at async TemplateBuilderTextArtifactWorkerClient.renderTextArtifact (C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:131047:25)
    at async TemplateBuilderTextArtifactService.render (C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:131206:20)
    at async C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:29334:28
    at async C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:29799:17
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 11:01:36   ERROR [ExceptionsHandler] Plugin 'electron-bridge' is unavailable: HTTP 404 for https://registry.npmjs.org/@ffprobe-installer/win32-x64/-/win32-x64-5.0.1.tgz
PluginHostUnavailableError: Plugin 'electron-bridge' is unavailable: HTTP 404 for https://registry.npmjs.org/@ffprobe-installer/win32-x64/-/win32-x64-5.0.1.tgz
    at ElectronPluginHost.parseResponse (C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:114995:15)
    at process.processTicksAndRejections (node:internal/process/task_queues:95:5)
    at async ElectronPluginHost.ensureStarted (C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:114954:21)
    at async TemplateBuilderTextArtifactWorkerClient.renderTextArtifact (C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:131047:25)
    at async TemplateBuilderTextArtifactService.render (C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:131206:20)
    at async C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:29334:28
    at async C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:29799:17
[nestjs] [Nest] 6940  - 2026. 05. 20. 오전 11:01:36   ERROR [ExceptionsHandler] Plugin 'electron-bridge' is unavailable: HTTP 404 for https://registry.npmjs.org/@ffprobe-installer/win32-x64/-/win32-x64-5.0.1.tgz
PluginHostUnavailableError: Plugin 'electron-bridge' is unavailable: HTTP 404 for https://registry.npmjs.org/@ffprobe-installer/win32-x64/-/win32-x64-5.0.1.tgz
    at ElectronPluginHost.parseResponse (C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:114995:15)
    at process.processTicksAndRejections (node:internal/process/task_queues:95:5)
    at async ElectronPluginHost.ensureStarted (C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:114954:21)
    at async TemplateBuilderTextArtifactWorkerClient.renderTextArtifact (C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:131047:25)
    at async TemplateBuilderTextArtifactService.render (C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:131206:20)
    at async C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:29334:28
    at async C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:29799:17
    ....
[nestjs] exited (code=0)
  ```

  ## App / UI Observations

  ```text
템플릿 빌더 테스트해봤는데 기존 템플릿들 조회는 잘
  되고(다만 맥에서 빌드한거 테스트해봤을 때보다 폰트들이 조금 더 두껍게 보이는 것 같은데 왜그런지 잘 모르겠어) 근데 새
  템플릿을 생성한 뒤에 메인 타이틀의 폰트를 로컬에 있던걸로 바꿔봤는데 아무런 변화가 없었어. ttf, otf 둘다 동일하게.
  preview 에서 전혀 폰트가 바뀌지 않았어. 그리고 새 템플릿을 생성한 후에 템플릿 목록 그리드에 추가된 카드 썸네일에 엑박
  이 있었어. 일단 거기까지 템플릿 빌더 테스트해봤고, 플러그인 스토어에서 '안무 영상 하이라이트 추출' 플러그인을 선택 후
  '설치하기' 버튼을 눌렀고 ffmpeg, ffprobe 설치해야한다는 오버레이가 떴고 '다운로드' 버튼을 눌렀는데, 에러가 났어.
  ```

  ## Errors

  ```text
  다운로드 실패
  Error: Error invoking remote method 'clipper:download:startFfmpeg': Error: HTTP 404 for
  https://registry.npmjs.org/@ffprobe-installer/win32-x64/-/win32-x64-5.0.1.tgz

  NestJS 터미널 에러 출력:

  [nestjs] [Nest] 6940  - 2026. 05. 20. 오전 11:01:36   ERROR [ExceptionsHandler] Plugin 'electron-bridge' is unavailable: HTTP 404 for https://registry.npmjs.org/@ffprobe-installer/win32-x64/-/win32-x64-5.0.1.tgz
PluginHostUnavailableError: Plugin 'electron-bridge' is unavailable: HTTP 404 for https://registry.npmjs.org/@ffprobe-installer/win32-x64/-/win32-x64-5.0.1.tgz
    at ElectronPluginHost.parseResponse (C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:114995:15)
    at process.processTicksAndRejections (node:internal/process/task_queues:95:5)
    at async ElectronPluginHost.ensureStarted (C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:114954:21)
    at async TemplateBuilderTextArtifactWorkerClient.renderTextArtifact (C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:131047:25)
    at async TemplateBuilderTextArtifactService.render (C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:131206:20)
    at async C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:29334:28
    at async C:\Users\bb\Desktop\project\clipper2\clipper2-smoke-install\resources\clipper_nestjs\index.js:29799:17
  ```

  ## main.log

  ```text
[2026-05-20 10:51:27] [info] [uv sync] + watchfiles==1.1.1
 + wcwidth==0.6.0
 +
[2026-05-20 10:51:27] [info] [uv sync] websockets==16.0
 + yt-dlp==2026.3.17
[2026-05-20 10:51:28] [info] [setup] Python env ready.
[2026-05-20 10:51:28] [info] [PluginHostBridge] listening on http://127.0.0.1:52264
[2026-05-20 10:51:28] [info] [window] showing main window
[2026-05-20 10:51:29] [info] [NestManager] ready at http://127.0.0.1:52267/v1
[2026-05-20 10:53:11] [info] [ffmpeg] Downloading ffmpeg for win32-x64…
[2026-05-20 10:53:16] [info] [ffmpeg] ffmpeg ready → C:\Users\bb\AppData\Roaming\Clipper2\bin\ffmpeg.exe
[2026-05-20 10:53:16] [info] [ffmpeg] Downloading ffprobe for win32-x64…
[2026-05-20 10:53:17] [info] [ffmpeg] Downloading ffprobe for win32-x64…
[2026-05-20 10:53:17] [info] [ffmpeg] Downloading ffprobe for win32-x64…
...
[2026-05-20 11:02:01] [info] [ffmpeg] Downloading ffprobe for win32-x64…
[2026-05-20 11:02:01] [info] [ffmpeg] Downloading ffprobe for win32-x64…
[2026-05-20 11:02:14] [info] [ffmpeg] Downloading ffprobe for win32-x64…
[2026-05-20 11:02:14] [error] Error occurred in handler for 'clipper:download:startFfmpeg': Error: HTTP 404 for https://registry.npmjs.org/@ffprobe-installer/win32-x64/-/win32-x64-5.0.1.tgz
[2026-05-20 11:03:17] [info] [ffmpeg] Downloading ffprobe for win32-x64…
[2026-05-20 11:03:17] [info] [ffmpeg] Downloading ffprobe for win32-x64…
...
[2026-05-20 11:03:20] [info] [ffmpeg] Downloading ffprobe for win32-x64…
[2026-05-20 11:03:20] [info] [ffmpeg] Downloading ffprobe for win32-x64…
[2026-05-20 11:03:20] [info] [ffmpeg] Downloading ffprobe for win32-x64…
[2026-05-20 11:03:23] [info] [nestjs] exited (code=0)
  ```
