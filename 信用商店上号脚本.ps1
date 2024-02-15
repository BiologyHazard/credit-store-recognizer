# param (
#     [int]$start_from
# )

$package_name = @{"�ٷ�"="com.hypergryph.arknights"; "b��"="com.hypergryph.arknights.bilibili"}
$activity_name = "com.u8.sdk.U8UnityContext"

$MuMuManager = "D:\Program Files\Netease\MuMuPlayer-12.0\shell\MuMuManager.exe"
$emulator_index = 4
$MuMuShared_folder = "C:\Users\Administrator\Documents\MuMu�����ļ���\Screenshots"
$screenshot_folder = "D:\BioHazard\Documents\Arknights\�����̵�ͳ��\�����̵��ͼ"

function single_account {
    param (
        [string]$index,
        [string]$server,
        [string]$nickname,
        [string]$phone,
        [string]$password
    )

    echo $index-$server-$nickname

    if ((& $MuMuManager api -v $emulator_index player_state | findstr check) -ne "check player state: state=start_finished") {
        & $MuMuManager api -v $emulator_index launch_player
        sleep 30
    }

    $address = & $MuMuManager adb -v $emulator_index

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

    if ($server -eq "�ٷ�") {
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
    else {  # b��
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

    # adb -s $address shell input tap 793 717  # ͬ��Э��
    # sleep 1
    # adb -s $address shell input tap 971 819
    # sleep 4

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
    $filename = "CreditStore-$datetime-$index-$server-$nickname.png"
    $android_path = "/storage/emulated/0/`$MuMu12Shared/Screenshots/$filename"
    $windows_source_path = "$MuMuShared_folder\$filename"
    $windows_destination_path = "$screenshot_folder"
    adb -s $address shell screencap "'$android_path'"
    if (-not (Test-Path $windows_destination_path)) {
        New-Item -ItemType Directory -Path $windows_destination_path
    }
    # adb -s $address pull $android_path $windows_path
    Move-Item -Path $windows_source_path -Destination $windows_destination_path
    adb -s $address shell am force-stop $package_name.$server
}

$player_list = @(
)
$start_from = 0

$csv = Import-Csv -Path "D:\BioHazard\Documents\Arknights\�����̵�ͳ��\accounts.csv" -Encoding UTF8 -Delimiter `t
foreach ($row in $csv) {
    $index = $row.���
    $server = $row.����
    $nickname = $row.�ǳ�
    $phone = $row.�˺�
    $password = $row.����
    $���������̵���� = $row.���������̵����
    $Ҫ�Ϻ� = $row.Ҫ�Ϻ�
    if (-not ($server -and $nickname -and $phone -and $password)) {
        continue
    }
    if (-not ($���������̵���� -eq "TRUE" -and $Ҫ�Ϻ� -eq "TRUE")) {
        continue
    }
    if ($player_list -and ($player_list -notcontains [int]$index)) {
        continue
    }
    if ([int]$index -lt $start_from) {
        continue
    }
    single_account $index $server $nickname $phone $password
}
