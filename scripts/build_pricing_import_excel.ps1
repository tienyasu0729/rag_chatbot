param(
    [string]$CategoriesCsv = 'D:\Workspace\user-cars-repository\repo-design\dataset_cleaner\data_migrator\json_to_csv\output\categories.csv',
    [string]$SubcategoriesCsv = 'D:\Workspace\user-cars-repository\repo-design\dataset_cleaner\data_migrator\json_to_csv\output\subcategories.csv',
    [string]$OutputDir = 'C:\Users\VAN-NAM\Downloads\dinhgiaxe_import_bundle',
    [string]$OutputFileName = 'vehicle_pricing_import_toyota_vios_2021_select.xlsx'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Convert-ToExcelColumnName {
    param([int]$ColumnNumber)

    $name = ''
    while ($ColumnNumber -gt 0) {
        $remainder = ($ColumnNumber - 1) % 26
        $name = [char](65 + $remainder) + $name
        $ColumnNumber = [math]::Floor(($ColumnNumber - 1) / 26)
    }
    return $name
}

function Set-Cell {
    param(
        [object]$Sheet,
        [int]$Row,
        [int]$Column,
        [object]$Value
    )

    $Sheet.Cells.Item($Row, $Column).Value2 = $Value
}

function Decode-Utf8Base64 {
    param([string]$Value)

    return [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Value))
}

if (-not (Test-Path -LiteralPath $CategoriesCsv)) {
    throw "Khong tim thay categories.csv: $CategoriesCsv"
}

if (-not (Test-Path -LiteralPath $SubcategoriesCsv)) {
    throw "Khong tim thay subcategories.csv: $SubcategoriesCsv"
}

if (-not (Test-Path -LiteralPath $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

$outputPath = Join-Path $OutputDir $OutputFileName

$categories = Import-Csv -LiteralPath $CategoriesCsv | Where-Object { $_.name -and $_.status -eq 'active' }
$subcategories = Import-Csv -LiteralPath $SubcategoriesCsv | Where-Object { $_.name -and $_.status -eq 'active' }

$vehicleFields = @(
    @{ field = 'categoryName'; value = '' }
    @{ field = 'subcategoryName'; value = '' }
    @{ field = 'title'; value = 'Toyota Vios G 1.5 CVT 2021' }
    @{ field = 'year'; value = 2021 }
    @{ field = 'mileage'; value = 80000 }
    @{ field = 'fuel'; value = Decode-Utf8Base64 'WMSDbmc=' }
    @{ field = 'transmission'; value = Decode-Utf8Base64 'VOG7sSDEkeG7mW5n' }
    @{ field = 'bodyStyle'; value = 'Sedan' }
    @{ field = 'origin'; value = Decode-Utf8Base64 'VHJvbmcgbsaw4bubYw==' }
    @{ field = 'description'; value = Decode-Utf8Base64 'WGUgdMawIG5ow6JuIG3DoHUgYuG6oWMsIE9ETyA4MC4wMDAga20sIG5nxrDhu51pIGLDoW4gY2FtIGvhur90IGtow7VuZyBs4buXaS4=' }
)

$imageRows = @(
    @{ fileName = 'front.jpg'; declaredGroup = 'front'; caption = Decode-Utf8Base64 '4bqibmggxJHhuqd1IHhlIHThu5VuZyBxdWFu'; captionBy = 'manager'; captionType = 'user_note' }
    @{ fileName = 'front_chech_trai.jpg'; declaredGroup = 'front'; caption = Decode-Utf8Base64 '4bqibmggxJHhuqd1IHhlIGNow6lvIHRyw6Fp'; captionBy = 'manager'; captionType = 'user_note' }
    @{ fileName = 'duoi_xe.jpg'; declaredGroup = 'rear'; caption = Decode-Utf8Base64 '4bqibmggxJF1w7RpIHhl'; captionBy = 'manager'; captionType = 'user_note' }
    @{ fileName = 'left_side_gan_dung.jpg'; declaredGroup = 'left_side'; caption = Decode-Utf8Base64 '4bqibmggaMO0bmcgdHLDoWk='; captionBy = 'manager'; captionType = 'user_note' }
    @{ fileName = 'right_side_gan_dung.jpg'; declaredGroup = 'right_side'; caption = Decode-Utf8Base64 '4bqibmggaMO0bmcgcGjhuqNp'; captionBy = 'manager'; captionType = 'user_note' }
    @{ fileName = 'interior_front.jpg'; declaredGroup = 'interior_front'; caption = Decode-Utf8Base64 '4bqibmggbuG7mWkgdGjhuqV0IHRyxrDhu5tj'; captionBy = 'manager'; captionType = 'user_note' }
    @{ fileName = 'interior_rear.jpg'; declaredGroup = 'interior_rear'; caption = Decode-Utf8Base64 '4bqibmggbuG7mWkgdGjhuqV0IHNhdQ=='; captionBy = 'manager'; captionType = 'user_note' }
    @{ fileName = 'document.jpg'; declaredGroup = 'document'; caption = Decode-Utf8Base64 '4bqibmggZ2nhuqV5IHThu50geGU='; captionBy = 'manager'; captionType = 'user_note' }
)

$xlValidateList = 3
$xlValidAlertStop = 1
$xlBetween = 1
$xlSheetVisible = -1
$xlSheetHidden = 0
$xlOpenXMLWorkbook = 51

$excel = $null
$workbook = $null

try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false

    $workbook = $excel.Workbooks.Add()
    while ($workbook.Worksheets.Count -lt 4) {
        $null = $workbook.Worksheets.Add()
    }

    $vehicleSheet = $workbook.Worksheets.Item(1)
    $imagesSheet = $workbook.Worksheets.Item(2)
    $lookupCategoriesSheet = $workbook.Worksheets.Item(3)
$lookupSubcategoriesSheet = $workbook.Worksheets.Item(4)

    $vehicleSheet.Name = 'Vehicle'
    $imagesSheet.Name = 'Images'
    $lookupCategoriesSheet.Name = 'LookupCategories'
    $lookupSubcategoriesSheet.Name = 'LookupSubcategories'

    $workbook.Worksheets | ForEach-Object {
        $_.Cells.Font.Name = 'Arial'
        $_.Cells.Font.Size = 11
    }

    Set-Cell -Sheet $vehicleSheet -Row 1 -Column 1 -Value 'field'
    Set-Cell -Sheet $vehicleSheet -Row 1 -Column 2 -Value 'value'
    for ($i = 0; $i -lt $vehicleFields.Count; $i++) {
        Set-Cell -Sheet $vehicleSheet -Row ($i + 2) -Column 1 -Value $vehicleFields[$i].field
        Set-Cell -Sheet $vehicleSheet -Row ($i + 2) -Column 2 -Value $vehicleFields[$i].value
    }

    $vehicleSheet.Columns.Item('A:B').EntireColumn.AutoFit() | Out-Null
    $vehicleSheet.Range('A1:B1').Font.Bold = $true
    $vehicleSheet.Range('A1:B1').Interior.Color = 15132390
    Set-Cell -Sheet $imagesSheet -Row 1 -Column 1 -Value 'fileName'
    Set-Cell -Sheet $imagesSheet -Row 1 -Column 2 -Value 'declaredGroup'
    Set-Cell -Sheet $imagesSheet -Row 1 -Column 3 -Value 'caption'
    Set-Cell -Sheet $imagesSheet -Row 1 -Column 4 -Value 'captionBy'
    Set-Cell -Sheet $imagesSheet -Row 1 -Column 5 -Value 'captionType'
    for ($i = 0; $i -lt $imageRows.Count; $i++) {
        $row = $i + 2
        Set-Cell -Sheet $imagesSheet -Row $row -Column 1 -Value $imageRows[$i].fileName
        Set-Cell -Sheet $imagesSheet -Row $row -Column 2 -Value $imageRows[$i].declaredGroup
        Set-Cell -Sheet $imagesSheet -Row $row -Column 3 -Value $imageRows[$i].caption
        Set-Cell -Sheet $imagesSheet -Row $row -Column 4 -Value $imageRows[$i].captionBy
        Set-Cell -Sheet $imagesSheet -Row $row -Column 5 -Value $imageRows[$i].captionType
    }
    $imagesSheet.Columns.Item('A:E').EntireColumn.AutoFit() | Out-Null
    $imagesSheet.Range('A1:E1').Font.Bold = $true
    $imagesSheet.Range('A1:E1').Interior.Color = 15132390

    Set-Cell -Sheet $lookupCategoriesSheet -Row 1 -Column 1 -Value 'name'
    Set-Cell -Sheet $lookupCategoriesSheet -Row 1 -Column 2 -Value 'rangeKey'
    for ($i = 0; $i -lt $categories.Count; $i++) {
        $row = $i + 2
        $category = $categories[$i]
        $rangeKey = "Cat_$($category.id)"
        Set-Cell -Sheet $lookupCategoriesSheet -Row $row -Column 1 -Value $category.name
        Set-Cell -Sheet $lookupCategoriesSheet -Row $row -Column 2 -Value $rangeKey
    }

    $categoryLastRow = $categories.Count + 1
    $workbook.Names.Add('CategoryOptions', "='LookupCategories'!`$A`$2:`$A`$$categoryLastRow") | Out-Null

    Set-Cell -Sheet $lookupSubcategoriesSheet -Row 1 -Column 1 -Value 'name'
    $sortedSubcategories = @($subcategories | Sort-Object -Property name)
    for ($i = 0; $i -lt $sortedSubcategories.Count; $i++) {
        Set-Cell -Sheet $lookupSubcategoriesSheet -Row ($i + 2) -Column 1 -Value $sortedSubcategories[$i].name
    }
    $subcategoriesLastRow = $sortedSubcategories.Count + 1
    $workbook.Names.Add('SubcategoryOptions', "='LookupSubcategories'!`$A`$2:`$A`$$subcategoriesLastRow") | Out-Null

    $vehicleSheet.Range('B2').Validation.Delete()
    $vehicleSheet.Range('B2').Validation.Add($xlValidateList, $xlValidAlertStop, $xlBetween, '=CategoryOptions') | Out-Null
    $vehicleSheet.Range('B2').Validation.IgnoreBlank = $true
    $vehicleSheet.Range('B2').Validation.InCellDropdown = $true
    $vehicleSheet.Range('B2').Validation.ErrorTitle = Decode-Utf8Base64 'R2nDoSB0cuG7iyBraMO0bmcgaOG7o3AgbOG7hw=='
    $vehicleSheet.Range('B2').Validation.ErrorMessage = Decode-Utf8Base64 'SMOjeSBjaOG7jW4gaMOjbmcgeGUgdOG7qyBkYW5oIHPDoWNoLg=='

    $vehicleSheet.Range('B3').Validation.Delete()
    $vehicleSheet.Range('B3').Validation.Add($xlValidateList, $xlValidAlertStop, $xlBetween, '=SubcategoryOptions') | Out-Null
    $vehicleSheet.Range('B3').Validation.IgnoreBlank = $true
    $vehicleSheet.Range('B3').Validation.InCellDropdown = $true
    $vehicleSheet.Range('B3').Validation.ErrorTitle = Decode-Utf8Base64 'R2nDoSB0cuG7iyBraMO0bmcgaOG7o3AgbOG7hw=='
    $vehicleSheet.Range('B3').Validation.ErrorMessage = Decode-Utf8Base64 'SMOjeSBjaOG7jW4gZMOybmcgeGUgdGh14buZYyBow6NuZyDEkcOjIGNo4buNbi4='

    $lookupCategoriesSheet.Visible = $xlSheetHidden
    $lookupSubcategoriesSheet.Visible = $xlSheetHidden
    $vehicleSheet.Visible = $xlSheetVisible
    $imagesSheet.Visible = $xlSheetVisible
    $vehicleSheet.Activate() | Out-Null

    if (Test-Path -LiteralPath $outputPath) {
        Remove-Item -LiteralPath $outputPath -Force
    }

    $workbook.SaveAs($outputPath, $xlOpenXMLWorkbook)
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

Write-Output ("{0}{1}" -f (Decode-Utf8Base64 'xJDDoyB04bqhbyBmaWxlOiA='), $outputPath)
