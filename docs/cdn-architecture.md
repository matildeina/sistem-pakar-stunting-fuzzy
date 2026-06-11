# CDN Architecture — TumbuhCerah

## Rancangan Arsitektur CDN

| Komponen | Provider | Detail |
|----------|----------|--------|
| CDN Layer | AWS CloudFront | Di depan EC2 sebagai edge cache |
| Origin Server | AWS EC2 | `32.236.142.31` (ap-southeast-2) |
| Static Assets | Azure Blob Storage | `tumbuhcerahstorage01.blob.core.windows.net` |
| Container | `foto-anak` | Foto anak hasil konsultasi |

## Arsitektur Flow

## Konfigurasi CloudFront (Rancangan)

- Origin Domain: `32.236.142.31`
- Protocol: HTTP → HTTPS redirect
- Cache Policy: CachingDisabled (dynamic content)
- Price Class: PriceClass_All (global edge)

## Konfigurasi Azure CDN (Rancangan)

- Profile: `tumbuhcerah-cdn`
- Endpoint: `tumbuhcerah.azureedge.net`
- Origin: `tumbuhcerahstorage01.blob.core.windows.net`
- Container: `foto-anak`

## Keterbatasan

AWS CloudFront dan Azure CDN memerlukan verifikasi akun
tambahan yang tidak tersedia pada akun AWS Educate / 
Azure for Students. Arsitektur dan konfigurasi sudah 
dirancang dan didokumentasikan di atas.

## Multi-Cloud Architecture

| Layer | Provider |
|-------|----------|
| Compute (EC2) | AWS |
| Container (Docker) | AWS EC2 |
| Object Storage | Azure Blob Storage |
| CDN (Rancangan) | AWS CloudFront + Azure CDN |
| VPC Segmentasi | AWS (4 VPC) |