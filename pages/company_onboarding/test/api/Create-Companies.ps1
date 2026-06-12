<#
.SYNOPSIS
    Creates 2 companies using the Rhythm ERP Company Onboarding FastAPI endpoint.

.DESCRIPTION
    This script uses a Bearer token (captured from Chrome DevTools) to create
    2 companies via the POST /core/dynamic-screen-wrapper/ endpoint.

    Each run generates UNIQUE company data (names, PAN, CIN, GSTIN, email, phone)
    using timestamps and random characters so you can run it multiple times.

    How to get the token:
      1. Open ERP in Chrome -> F12 -> Network tab
      2. Click any XHR request to /core/...
      3. Copy the Authorization header value (after "Bearer ")

.EXAMPLE
    .\Create-Companies.ps1
#>

# ============================================================
# CONFIGURATION
# ============================================================
$BaseUrl      = "https://rhythmerp.algorhythms.in"
$TenantId     = "681"

# Paste your Bearer token here (captured from Chrome DevTools -> Network -> Authorization header)
$BearerToken  = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzgxMjYwMjk4LCJpYXQiOjE3ODEyNDU4OTgsImp0aSI6Ijg4MTg3YzE5NTQ1YjQzYTM5MmZjMGVkODNjNGQ3ZDQyIiwidXNlcl9pZCI6IjE4MSJ9.Do8Iizl157k2MlgMbujtp5ffdrTSHXtDwFQbH_iQYUc"

# Strip "Bearer " prefix if user pasted the full header
if ($BearerToken.StartsWith("Bearer ")) {
    $BearerToken = $BearerToken.Substring(7)
}

# ============================================================
# HELPER FUNCTIONS - Generate unique data
# ============================================================
$rand = [System.Random]::new()

function Get-RandomLetters([int]$count) {
    $sb = [System.Text.StringBuilder]::new()
    for ($j = 0; $j -lt $count; $j++) {
        $ch = [char](65 + $rand.Next(26))
        $sb.Append($ch) | Out-Null
    }
    return $sb.ToString()
}

function Get-RandomDigits([int]$count) {
    $sb = [System.Text.StringBuilder]::new()
    for ($j = 0; $j -lt $count; $j++) {
        $ch = [char](48 + $rand.Next(10))
        $sb.Append($ch) | Out-Null
    }
    return $sb.ToString()
}

function Get-UniqueSuffix {
    $ts = Get-Date -Format "HHmmss"
    $letters = Get-RandomLetters 3
    return "${ts}${letters}"
}

function New-Pan {
    # Format: ABCDE1234F
    $letters = Get-RandomLetters 5
    $digits = Get-RandomDigits 4
    $last = Get-RandomLetters 1
    return "${letters}${digits}${last}"
}

function New-Cin {
    # Format: U12345MH2024PTC123456
    $digits1 = Get-RandomDigits 5
    $year = @(2020, 2021, 2022, 2023, 2024, 2025)[$rand.Next(6)]
    $digits2 = Get-RandomDigits 6
    return "U${digits1}MH${year}PTC${digits2}"
}

function New-Gstin {
    # Format: 27ABCDE1234A1Z5
    $stateCodes = @("27", "29", "33", "24", "08")
    $stateCode = $stateCodes[$rand.Next($stateCodes.Count)]
    $panPart = Get-RandomLetters 5
    $panDigits = Get-RandomDigits 4
    return "${stateCode}${panPart}${panDigits}A1Z5"
}

function New-Phone {
    $prefixes = @("6", "7", "8", "9")
    $p = $prefixes[$rand.Next($prefixes.Count)]
    return "${p}$(Get-RandomDigits 9)"
}

# ============================================================
# SETUP HEADERS
# ============================================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Rhythm ERP - Company Onboarding API" -ForegroundColor Cyan
Write-Host "  Creating 2 Companies via FastAPI" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$tokenPreview = $BearerToken.Substring(0, [Math]::Min(30, $BearerToken.Length))
Write-Host "(1/3) Using Bearer Token: $tokenPreview..." -ForegroundColor Green

$apiHeaders = @{
    "Authorization" = "Bearer $BearerToken"
    "X-Tenant-ID"   = $TenantId
    "Content-Type"  = "application/json"
}

# ============================================================
# STEP 2: BUILD UNIQUE COMPANY PAYLOADS
# ============================================================
Write-Host ""
Write-Host "(2/3) Building company payloads (unique data)..." -ForegroundColor Yellow

$prefixes = @("Apex", "Zenith", "Nova", "Pulse", "Vertex", "Orion", "Nexus", "Prism", "Crest", "Forge", "Ember", "Atlas", "Solaris", "Quantum", "Helix", "Titan")
$middles  = @("Global", "Prime", "Digital", "Smart", "Green", "Royal", "Elite", "Premium", "East", "West", "North", "South", "Central")
$suffixes = @("Technologies", "Industries", "Enterprises", "Solutions", "Systems", "Services", "Corporation", "Holdings", "Group", "Ventures", "Innovations", "Dynamics")

$firstNames = @("Aarav", "Vivaan", "Aditya", "Vedant", "Arjun", "Sai", "Rohan", "Amit", "Nikhil", "Prashant", "Priya", "Pooja", "Sneha", "Neha", "Anita", "Kavita")
$lastNames  = @("Sharma", "Patil", "Desai", "Joshi", "Kulkarni", "Mehta", "Shah", "Pawar", "Jadhav", "Chavan", "Bhosale", "More", "Kale", "Gaikwad")

$promoterPool = @(
    @{ promoter_name = "Mr Chaitnya Namdev Chavhan"; remark = "Mr Chavhan." },
    @{ promoter_name = "Mr Durgesh Vishnu Bankar";   remark = "Mr Bankar." },
    @{ promoter_name = "Mr Amit Ramesh Sharma";      remark = "Mr Sharma." },
    @{ promoter_name = "Mr Suresh Dnyaneshwar Patil"; remark = "Mr Patil." },
    @{ promoter_name = "Mr Rajesh Bhimrao Jadhav";   remark = "Mr Jadhav." },
    @{ promoter_name = "Mr Vikram Anil Deshmukh";    remark = "Mr Deshmukh." }
)

$backgrounds = @(
    "Software development and IT consulting services with focus on enterprise solutions and cloud infrastructure",
    "Manufacturing and industrial solutions specializing in precision engineering and quality control systems",
    "Financial services and banking operations with digital transformation capabilities",
    "Healthcare and pharmaceutical research with biotech innovation focus",
    "E-commerce and digital retail platforms with supply chain optimization",
    "Telecommunications and networking infrastructure with 5G deployment expertise",
    "Education and e-learning technology solutions with AI-driven personalization",
    "Logistics and supply chain management with real-time tracking systems"
)

$infraLocations = @(
    "Main Market Yard, Agricultural Produce",
    "Rural Hub Center, District HQ",
    "Cooperative Society Building, Taluka",
    "Agricultural Processing Unit, Industrial Area",
    "FPC Operations Center, Village Panchayat"
)

# Infrastructure types: 1585=Office, 1584=Warehouse, 1877=Cold Storage, 1878=Processing, 1879=Other
$infraTypes = @(1585, 1584, 1877, 1878, 1879)
# Ownership: 530=Owned, 531=Leased
$ownershipTypes = @(530, 531)

# Address cascading FK IDs (verified on tenant 599)
# Maharashtra=98, Pune=480, Haveli=11542
# Gujarat: Ahmadabad=271, Ahmadabad City=1192
# Karnataka: Bengaluru Urban=166, Anekal=5197
$addressOptions = @(
    @{ address_type_ref_id = 1649; country = 8; state = 98;  district = 480;  taluka = 11542; pin_code = "411001"; area = "Haveli" },
    @{ address_type_ref_id = 1649; country = 8; state = 98;  district = 480;  taluka = 11542; pin_code = "411002"; area = "Baramati" },
    @{ address_type_ref_id = 1649; country = 8; state = 98;  district = 480;  taluka = 11542; pin_code = "411003"; area = "Mulshi" },
    @{ address_type_ref_id = 1649; country = 8; state = 98;  district = 480;  taluka = 11542; pin_code = "411004"; area = "Maval" },
    @{ address_type_ref_id = 1649; country = 8; state = 98;  district = 480;  taluka = 11542; pin_code = "411005"; area = "Junnar" }
)

function New-CompanyPayload([string]$companyIndex) {
    $suffix = Get-UniqueSuffix

    # Pick random components
    $prefix = $prefixes[$rand.Next($prefixes.Count)]
    $middle = $middles[$rand.Next($middles.Count)]
    $suffixWord = $suffixes[$rand.Next($suffixes.Count)]
    $companyName = "${prefix} ${middle} ${suffixWord}"

    $shortName = "${prefix}${middle}${suffixWord}"
    if ($shortName.Length -gt 9) { $shortName = $shortName.Substring(0, 9) }

    $code = "${prefix}${middle}"
    if ($code.Length -gt 4) { $code = $code.Substring(0, 4) }
    $code = $code.ToUpper()

    $firstName = $firstNames[$rand.Next($firstNames.Count)]
    $lastName  = $lastNames[$rand.Next($lastNames.Count)]
    $contactName = "${firstName} ${lastName}"

    $emailLocalFirst = $firstName.ToLower()
    $emailLocalLast  = $lastName.ToLower()
    $email = "${emailLocalFirst}.${emailLocalLast}${suffix}@testmail.com"
    $phone = New-Phone
    $pan = New-Pan
    $cin = New-Cin
    $gstin = New-Gstin
    $background = $backgrounds[$rand.Next($backgrounds.Count)]

    # Pick 2 random promoters
    $shuffled = $promoterPool | Sort-Object { $rand.Next() }
    $promoters = @($shuffled[0], $shuffled[1])

    # Pick random address
    $addr = $addressOptions[$rand.Next($addressOptions.Count)]

    # Pick random infrastructure
    $infraType = $infraTypes[$rand.Next($infraTypes.Count)]
    $ownership = $ownershipTypes[$rand.Next($ownershipTypes.Count)]
    $infraLoc = $infraLocations[$rand.Next($infraLocations.Count)]

    $payload = @{
        id             = ""
        attribute_name = "Company Onboarding"
        name           = $companyName
        user_type_id   = 12
        parent_id      = $null
        tenant_linked  = @()
        level          = "2"
        is_parent      = $false
        children       = @(
            @{
                stepper_name           = "Company Details"
                is_stepper             = $true
                details                = @()
                children               = @()
                tenant_short_name      = $shortName
                tenant_code            = $code
                contact_person_name    = $contactName
                company_background     = $background
                email_id               = $email
                phone_no               = $phone
                pan_no                 = $pan
                tan_no                 = $null
                gst_no                 = $gstin
                cin_no                 = $cin
                plan_type_ref_id       = $null
                is_2fa_applicable      = $false
                authentication_type    = "email"
                base_currency          = 8
            },
            @{
                stepper_name = "Promoters Details"
                is_stepper   = $true
                details      = @($promoters[0], $promoters[1])
                children     = @()
            },
            @{
                stepper_name = "Address Details"
                is_stepper   = $true
                details      = @(
                    @{
                        address_type_ref_id = $addr.address_type_ref_id
                        country             = $addr.country
                        state               = $addr.state
                        district            = $addr.district
                        taluka              = $addr.taluka
                        address             = "$suffix, Test Street, $($addr.area)"
                        pin_code            = $addr.pin_code
                    }
                )
                children     = @()
            },
            @{
                stepper_name = "Business Activities"
                is_stepper   = $true
                details      = @(
                    @{
                        business_model                = "Agri-Input - Products and materials."
                        market_linkages               = "Market linkage involves connecting farmers."
                        line_of_business              = "Products and materials used by farmers."
                        additional_business_activities = "FPC carries out the business of Production."
                    }
                )
                children     = @()
            },
            @{
                stepper_name = "Infrastructure Details"
                is_stepper   = $true
                details      = @(
                    @{
                        infrastructure_type_ref_id = $infraType
                        location                  = $infraLoc
                        ownership_type            = $ownership
                        remarks                   = $null
                    }
                )
                children     = @()
            }
        )
    }

    return $payload
}

# Generate 2 unique companies
$company1 = New-CompanyPayload -companyIndex "1"
$company2 = New-CompanyPayload -companyIndex "2"
$companies = @($company1, $company2)

# Show what we're about to create
foreach ($c in $companies) {
    $details = $c.children[0]
    Write-Host "  -> $($c.name)" -ForegroundColor Gray
    Write-Host "     Code: $($details.tenant_code) | Email: $($details.email_id)" -ForegroundColor DarkGray
    Write-Host "     PAN: $($details.pan_no) | CIN: $($details.cin_no)" -ForegroundColor DarkGray
}

# ============================================================
# STEP 3: CREATE COMPANIES VIA API
# ============================================================
Write-Host ""
Write-Host "(3/3) Creating 2 companies via API..." -ForegroundColor Yellow
Write-Host "  Endpoint: POST $BaseUrl/core/dynamic-screen-wrapper/" -ForegroundColor Gray
Write-Host ""

$endpoint = "$BaseUrl/core/dynamic-screen-wrapper/"
$results  = @()

for ($i = 0; $i -lt $companies.Count; $i++) {
    $payload = $companies[$i]
    $companyName = $payload.name
    $jsonBody = $payload | ConvertTo-Json -Depth 10

    $num = $i + 1
    Write-Host "  ($num/2) Creating: $companyName" -ForegroundColor White -NoNewline

    try {
        $response = Invoke-RestMethod -Uri $endpoint -Method POST -Headers $apiHeaders -Body $jsonBody -ContentType "application/json"
        Write-Host " ... OK" -ForegroundColor Green
        $results += @{
            Company   = $companyName
            Status    = "SUCCESS"
            Response  = $response
        }
    }
    catch {
        # Extract detailed error message from the response body
        $errorMsg = $_.Exception.Message
        try {
            $errorStream = $_.Exception.Response.GetResponseStream()
            $reader = [System.IO.StreamReader]::new($errorStream)
            $errorBody = $reader.ReadToEnd()
            $reader.Close()
            $errorStream.Close()

            if ($errorBody) {
                try {
                    $errorData = $errorBody | ConvertFrom-Json
                    if ($errorData.errors) {
                        $errorMessages = @()
                        foreach ($e in $errorData.errors) {
                            $errorMessages += $e.error_message
                        }
                        $errorMsg = $errorMessages -join "; "
                    }
                    elseif ($errorData.message) {
                        $errorMsg = $errorData.message
                    }
                    elseif ($errorData.detail) {
                        $errorMsg = $errorData.detail
                    }
                    else {
                        $errorMsg = $errorBody.Substring(0, [Math]::Min(500, $errorBody.Length))
                    }
                }
                catch {
                    $errorMsg = $errorBody.Substring(0, [Math]::Min(500, $errorBody.Length))
                }
            }
        }
        catch {
            # Keep original error message if stream reading fails
        }

        Write-Host " ... FAILED" -ForegroundColor Red
        Write-Host "         Error: $errorMsg" -ForegroundColor Red
        $results += @{
            Company = $companyName
            Status  = "FAILED"
            Error   = $errorMsg
        }
    }

    # Small delay between requests to avoid rate limiting
    if ($i -lt $companies.Count - 1) {
        Start-Sleep -Milliseconds 300
    }
}

# ============================================================
# SUMMARY
# ============================================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RESULTS SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$successCount = ($results | Where-Object { $_.Status -eq "SUCCESS" }).Count
$failedCount  = ($results | Where-Object { $_.Status -eq "FAILED" }).Count

foreach ($r in $results) {
    if ($r.Status -eq "SUCCESS") {
        $icon = "(OK)"
        $color = "Green"
    } else {
        $icon = "(FAIL)"
        $color = "Red"
    }
    Write-Host "  $icon $($r.Company)" -ForegroundColor $color
    if ($r.Status -eq "FAILED" -and $r.Error) {
        Write-Host "       $($r.Error)" -ForegroundColor DarkRed
    }
}

Write-Host ""
Write-Host "  Total: $($results.Count) | Success: $successCount | Failed: $failedCount" -ForegroundColor White
Write-Host ""
