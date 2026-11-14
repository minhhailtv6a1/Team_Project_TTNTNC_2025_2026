param(
    [string]$Source = "Thuyet_trinh_Caro_AI_ban_chinh_sua.pptx",
    [string]$Candidate = "tmp/pptx_rework_build/Caro_AI_reworked_candidate.pptx"
)

$ErrorActionPreference = "Stop"

$project = (Resolve-Path -LiteralPath ".").Path
$sourcePath = (Resolve-Path -LiteralPath $Source).Path
$candidatePath = Join-Path $project $Candidate
$candidateDir = Split-Path -Parent $candidatePath
$uiImage = (Resolve-Path -LiteralPath "tmp/pptx_rework_assets/ui-ai-vs-ai.png").Path
$streamlitLogo = (Resolve-Path -LiteralPath "tmp/pptx_rework_assets/streamlit-logo.png").Path

New-Item -ItemType Directory -Path $candidateDir -Force | Out-Null
Copy-Item -LiteralPath $sourcePath -Destination $candidatePath -Force

function Update-TextRange {
    param($TextRange, [int]$SlideNumber)

    $text = $TextRange.Text
    $text = $text.Replace("–" + [char]0x00A0, "• ")
    $text = $text.Replace("2. Năm agent AI", "2. Các agent")
    $text = $text.Replace("Policy Network dự đoán nước đi, học từ Dataset của 3 teacher", "Policy Network dự đoán nước đi từ dataset của ba teacher")

    $replacements = @{
        "Năm agent AI" = "Các agent trong hệ thống"
        "Hai hướng tìm kiếm: Minimax và MCTS" = "Minimax và MCTS"
        "Thời gian Inference của Neural" = "Thời gian Inference của Policy v5"
        "Demo UI Streamlit" = "Giao diện Streamlit"
        "Calibrate budget theo phần cứng." = "Điều chỉnh budget theo phần cứng."
    }

    if ($replacements.ContainsKey($text)) {
        $text = $replacements[$text]
    }

    if ($SlideNumber -eq 20 -and $text.StartsWith("• Ba chế độ:")) {
        $text = @(
            "• Human vs Human, Human vs AI và AI vs AI."
            "• Chọn agent riêng cho X và O; Neural dùng checkpoint đã cấu hình."
            "• AI vs AI tự chạy từng nước đến cuối ván."
            "• UI hiển thị thời gian, nodes, simulations và tô đỏ đường thắng."
        ) -join "`r"
    }

    $TextRange.Text = $text
    $TextRange.Font.Name = "Arial"
}

function Update-ShapeCollection {
    param($Shapes, [int]$SlideNumber)

    foreach ($shape in $Shapes) {
        if ($shape.Type -eq 6) {
            Update-ShapeCollection -Shapes $shape.GroupItems -SlideNumber $SlideNumber
        }

        if ($shape.HasTextFrame -eq -1 -and $shape.TextFrame.HasText -eq -1) {
            Update-TextRange -TextRange $shape.TextFrame.TextRange -SlideNumber $SlideNumber
        }

        if ($shape.HasTable -eq -1) {
            for ($row = 1; $row -le $shape.Table.Rows.Count; $row++) {
                for ($column = 1; $column -le $shape.Table.Columns.Count; $column++) {
                    $cellRange = $shape.Table.Cell($row, $column).Shape.TextFrame.TextRange
                    Update-TextRange -TextRange $cellRange -SlideNumber $SlideNumber
                }
            }
        }
    }
}

$ppt = New-Object -ComObject PowerPoint.Application
$presentation = $null

try {
    $presentation = $ppt.Presentations.Open($candidatePath, $false, $false, $false)

    foreach ($slide in $presentation.Slides) {
        Update-ShapeCollection -Shapes $slide.Shapes -SlideNumber $slide.SlideIndex
    }

    $uiSlide = $presentation.Slides.Item(20)
    for ($index = $uiSlide.Shapes.Count; $index -ge 1; $index--) {
        $shape = $uiSlide.Shapes.Item($index)
        if ($shape.HasTextFrame -eq -1 -and $shape.TextFrame.HasText -eq -1) {
            if ($shape.TextFrame.TextRange.Text -like "Chèn ảnh chụp UI thật*") {
                $shape.Delete()
            }
        }
    }

    $screenshot = $uiSlide.Shapes.AddPicture($uiImage, $false, $true, 690, 118, 545, 341)
    $screenshot.Name = "Ảnh UI AI-vs-AI chạy thật"
    $screenshot.Line.Visible = -1
    $screenshot.Line.Weight = 0.75
    $screenshot.Line.ForeColor.RGB = 14342874

    $logo = $uiSlide.Shapes.AddPicture($streamlitLogo, $false, $true, 1090, 48, -1, -1)
    $logo.Name = "Logo Streamlit chính thức"
    $logo.LockAspectRatio = -1
    $logo.Width = 125

    $sourceNote = $uiSlide.Shapes.AddTextbox(1, 690, 468, 545, 24)
    $sourceNote.Name = "Nguồn ảnh UI"
    $sourceNote.TextFrame.TextRange.Text = "Ảnh chụp từ UI đang chạy trong repo. Logo: streamlit.io/brand."
    $sourceNote.TextFrame.TextRange.Font.Name = "Arial"
    $sourceNote.TextFrame.TextRange.Font.Size = 9
    $sourceNote.TextFrame.TextRange.Font.Color.RGB = 8421504

    foreach ($noteShape in $uiSlide.NotesPage.Shapes) {
        if ($noteShape.Type -eq 14 -and $noteShape.PlaceholderFormat.Type -eq 2 -and $noteShape.HasTextFrame -eq -1) {
            $noteShape.TextFrame.TextRange.Text = @(
                "Ảnh UI do nhóm chụp trực tiếp từ ứng dụng Streamlit của repository."
                "Logo Streamlit lấy từ trang brand chính thức: https://streamlit.io/brand"
                "Logo chỉ dùng để mô tả công nghệ của dự án; không hàm ý Streamlit tài trợ hoặc chứng thực."
            ) -join "`r"
            break
        }
    }

    $presentation.Save()
}
finally {
    if ($null -ne $presentation) {
        $presentation.Close()
        [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($presentation) | Out-Null
    }
    $ppt.Quit()
    [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($ppt) | Out-Null
}

Write-Output $candidatePath
