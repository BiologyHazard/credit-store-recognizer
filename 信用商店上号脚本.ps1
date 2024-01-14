$package_name = @{"官服"="com.hypergryph.arknights"; "b服"="com.hypergryph.arknights.bilibili"}
$activity_name = "com.u8.sdk.U8UnityContext"

$MuMuManager = "D:\Program Files\Netease\MuMuPlayer-12.0\shell\MuMuManager.exe"
$index = 4
$MuMuShared_folder = "C:\Users\Administrator\Documents\MuMu共享文件夹\Screenshots"
$screenshot_folder = "D:\BioHazard\Documents\Arknights\信用商店统计\信用商店截图"

function single_account {
    param (
        [string]$server,
        [string]$nickname,
        [string]$phone,
        [string]$password
    )

    echo $server-$nickname

    if ((& $MuMuManager api -v $index player_state | findstr check) -ne "check player state: state=start_finished") {
        & $MuMuManager api -v $index launch_player
        sleep 30
    }

    $address = & $MuMuManager adb -v $index

    adb connect $address
    # sleep 1
    # adb -s $address shell input keyevent 25
    # sleep 2
    adb -s $address shell am force-stop $package_name.$server
    # sleep 1
    adb -s $address shell am start -n "$($package_name.$server)/$activity_name"
    sleep 15

    adb -s $address shell input tap 960 540
    sleep 5

    if ($server -eq "官服") {
        adb -s $address shell input tap 1380 1020
        sleep 3
        adb -s $address shell input tap 960 750
        sleep 2
        adb -s $address shell input tap 1176 835
        sleep 2
        adb -s $address shell input tap 960 400
        sleep 2
        adb -s $address shell input text $phone
        sleep 2
        adb -s $address shell input tap 960 540
        sleep 2
        adb -s $address shell input text $password
        sleep 2
        # adb -s $address shell input tap 1080 180
        # sleep 2
        adb -s $address shell input tap 710 620
        sleep 2
        adb -s $address shell input tap 960 745
        sleep 20
    }
    else {  # b服
        adb -s $address shell input tap 1738 59
        sleep 1
        # adb -s $address shell input tap 960 466
        # sleep 1
        # adb -s $address shell input swipe 960 750 960 -750 300
        # sleep 1
        # adb -s $address shell input tap 960 730
        # sleep 1
        # adb -s $address shell input tap 960 590
        # sleep 20

        adb -s $address shell input tap 960 682
        sleep 1
        adb -s $address shell input tap 746 720
        sleep 1
        adb -s $address shell input tap 960 660
        sleep 1
        adb -s $address shell input tap 960 452

        adb -s $address shell input text $phone
        sleep 1
        adb -s $address shell input tap 960 550
        sleep 1
        adb -s $address shell input text $password
        sleep 1
        adb -s $address shell input tap 960 745
        sleep 20
    }

    adb -s $address shell input keyevent 111  # Esc
    sleep 1
    adb -s $address shell input keyevent 111
    sleep 1
    adb -s $address shell input keyevent 111
    sleep 1
    adb -s $address shell input keyevent 111
    sleep 1
    adb -s $address shell input keyevent 111
    sleep 1
    adb -s $address shell input tap 800 700
    sleep 2
    adb -s $address shell input tap 1260 720
    sleep 3
    adb -s $address shell input tap 1785 162
    sleep 3
    $datetime = Get-Date -Format "yyyyMMdd-HHmmss"
    $filename = "MuMu12-$datetime-$server-$nickname.png"
    $android_path = "/storage/emulated/0/`$MuMu12Shared/Screenshots/$filename"
    $windows_source_path = "$MuMuShared_folder\$filename"
    $windows_destination_path = "$screenshot_folder\$server-$nickname"
    adb -s $address shell screencap "'$android_path'"
    if (-not (Test-Path $windows_destination_path)) {
        New-Item -ItemType Directory -Path $windows_destination_path
    }
    # adb -s $address pull $android_path $windows_path
    Copy-Item -Path $windows_source_path -Destination $windows_destination_path
}

$player_list = @(
)

$csv = Import-Csv -Path "D:\BioHazard\Documents\Arknights\信用商店统计\accounts.csv" -Encoding UTF8 -Delimiter `t
foreach ($row in $csv) {
    $区服 = $row.区服
    $昵称 = $row.昵称
    $账号 = $row.账号
    $密码 = $row.密码
    if (-not ($区服 -and $昵称 -and $账号 -and $密码)) {
        continue
    }
    if ($player_list -and ($player_list -notcontains "$区服-$昵称")) {
        continue
    }
    single_account $区服 $昵称 $账号 $密码
}
