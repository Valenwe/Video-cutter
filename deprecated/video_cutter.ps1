param(
    [Parameter()]
    [String]$file,
    [Parameter()]
    [String]$frames,
    [Parameter()]
    [String]$json,
    [Parameter()]
    [int]$audio_track = 0
)

function Cut-Video {

    param (
        [string[]] $file,
        [string[]] $frames,
        [int]$audio_track
    )

    Write-Output "Cutting $file...";

    $filename = [System.IO.Path]::GetFileNameWithoutExtension($file);
    $timeframes = New-Object System.Collections.ArrayList;

    if ( $frames.Length -eq 1 ) {
        while (1) {
            $input_ab = Read-Host -Prompt "Enter <stop> or the timeframe in hh:mm:ss <a>/<b> ";

            if ( $input_ab -eq "stop" ) {
                break;
            }

            $new_input = $input_ab.Split("/");
            $timeframes.add($new_input) | out-null;
        }
    } else {
        $sub_frames = $frames.Split("_");
        for ($i = 0; $i -lt $sub_frames.Count; $i++) {
            $timeframes.add($sub_frames[$i].Split("/")) | out-null;
        }
    }
    
    for ($i = 0; $i -lt $timeframes.Count; $i++) {
        ffmpeg -i "$file" -ss $timeframes[$i][0] -to $timeframes[$i][1]  -map_chapters -1 -map 0:v:0 -map 0:a:$audio_track "$filename-$i.mp4";
    }
}

if ( -not($json.Length -eq 0 ) ) {
    while ( -not(Test-Path -Path $json -PathType Leaf) ) {
        $json = Read-Host -Prompt "$json cannot be found, please enter a correct path ";
    }

    $json_data = Get-Content $json | ConvertFrom-Json;

    foreach ($cut in $json_data) {
        Cut-Video -file $cut.file -frames $cut.frames -audio_track $audio_track;
    }

} else {
    if ( $file.Length -eq 0 ) {
        $file = Read-Host -Prompt "Enter the filename ";
    }

    while ( -not(Test-Path -Path $file -PathType Leaf) ) {
        $file = Read-Host -Prompt "$file cannot be found, please enter a correct path ";
    }

    Cut-Video -file $file -frames $frames -audio_track $audio_track;
}

