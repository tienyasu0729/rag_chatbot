param(
    [string]$WorkbookPath = 'C:\Users\VAN-NAM\Downloads\dinhgiaxe_import_bundle\vehicle_pricing_import_toyota_vios_2021_select.xlsx'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Decode-Utf8Base64 {
    param([string]$Value)
    [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($Value))
}

if (-not (Test-Path -LiteralPath $WorkbookPath)) {
    throw "Khong tim thay workbook: $WorkbookPath"
}

$excel = $null
$workbook = $null

try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false

    $workbook = $excel.Workbooks.Open($WorkbookPath)
    $vehicleSheet = $workbook.Worksheets.Item('Vehicle')
    $imagesSheet = $workbook.Worksheets.Item('Images')

    $imageRows = @(
        [pscustomobject]@{ fileName = 'front.jpg'; declaredGroup = 'front'; caption = Decode-Utf8Base64 '4bqibmggxJHhuqd1IHhlIHThu5VuZyBxdWFu'; captionBy = 'manager'; captionType = 'user_note' }
        [pscustomobject]@{ fileName = 'front_chech_trai.jpg'; declaredGroup = 'front'; caption = Decode-Utf8Base64 '4bqibmggxJHhuqd1IHhlIGNow6lvIHRyw6Fp'; captionBy = 'manager'; captionType = 'user_note' }
        [pscustomobject]@{ fileName = 'duoi_xe.jpg'; declaredGroup = 'rear'; caption = Decode-Utf8Base64 '4bqibmggxJF1w7RpIHhl'; captionBy = 'manager'; captionType = 'user_note' }
        [pscustomobject]@{ fileName = 'left_side_gan_dung.jpg'; declaredGroup = 'left_side'; caption = Decode-Utf8Base64 '4bqibmggaMO0bmcgdHLDoWk='; captionBy = 'manager'; captionType = 'user_note' }
        [pscustomobject]@{ fileName = 'right_side_gan_dung.jpg'; declaredGroup = 'right_side'; caption = Decode-Utf8Base64 '4bqibmggaMO0bmcgcGjhuqNp'; captionBy = 'manager'; captionType = 'user_note' }
        [pscustomobject]@{ fileName = 'interior_front.jpg'; declaredGroup = 'interior_front'; caption = Decode-Utf8Base64 '4bqibmggbuG7mWkgdGjhuqV0IHRyxrDhu5tj'; captionBy = 'manager'; captionType = 'user_note' }
        [pscustomobject]@{ fileName = 'interior_rear.jpg'; declaredGroup = 'interior_rear'; caption = Decode-Utf8Base64 '4bqibmggbuG7mWkgdGjhuqV0IHNhdQ=='; captionBy = 'manager'; captionType = 'user_note' }
        [pscustomobject]@{ fileName = 'document.jpg'; declaredGroup = 'document'; caption = Decode-Utf8Base64 '4bqibmggZ2nhuqV5IHThu50geGU='; captionBy = 'manager'; captionType = 'user_note' }
    )

    $imagesSheet.Cells.Clear()
    $headers = @('fileName', 'declaredGroup', 'caption', 'captionBy', 'captionType')
    for ($headerIndex = 0; $headerIndex -lt $headers.Count; $headerIndex++) {
        $imagesSheet.Cells.Item(1, $headerIndex + 1).Value2 = $headers[$headerIndex]
    }
    for ($rowIndex = 0; $rowIndex -lt $imageRows.Count; $rowIndex++) {
        $imagesSheet.Cells.Item($rowIndex + 2, 1).Value2 = $imageRows[$rowIndex].fileName
        $imagesSheet.Cells.Item($rowIndex + 2, 2).Value2 = $imageRows[$rowIndex].declaredGroup
        $imagesSheet.Cells.Item($rowIndex + 2, 3).Value2 = $imageRows[$rowIndex].caption
        $imagesSheet.Cells.Item($rowIndex + 2, 4).Value2 = $imageRows[$rowIndex].captionBy
        $imagesSheet.Cells.Item($rowIndex + 2, 5).Value2 = $imageRows[$rowIndex].captionType
    }
    $imagesSheet.Range('A1:E1').Font.Bold = $true
    $imagesSheet.Range('A1:E1').Interior.Color = 15132390
    $imagesSheet.Columns('A:E').AutoFit() | Out-Null

    $vehicleSheet.Cells.Item(11, 2).Value2 = Decode-Utf8Base64 'WGUgdMawIG5ow6JuIG3DoHUgYuG6oWMsIE9ETyA4MC4wMDAga20sIG5nxrDhu51pIGLDoW4gY2FtIGvhur90IGtow7VuZyBs4buXaS4='

    $workbook.Save()
}
finally {
    if ($workbook -ne $null) {
        $workbook.Close($true)
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($workbook) | Out-Null
    }
    if ($excel -ne $null) {
        $excel.Quit()
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

Write-Output "Da sua workbook: $WorkbookPath"
