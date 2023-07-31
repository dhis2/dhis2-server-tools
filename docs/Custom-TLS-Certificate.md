## Using a Custom SSL Certificate 
##### ENSURE YOU HAVE SSL/TLS Certificate and key beforehand
For HTTPS connection, the install used Letsencrypt to obtain an SSL/TLS certificate. This
should work fine most OS and browsers, however, these scripts provides a way of
using your own SSL/TLS certificates. To use your own custom SSL/TLS certs, follow below steps, 

1. Get/generate `customssl.crt` file which will be concatenating your certificate
   and any other intermediate and root certificates.
2. Get/generate `customssl.key` file, this contains private key used for certificate signing.
3. Copy these two files into `dhis2-server-tools/deploy/roles/proxy/files/` directory.
4. Edit `dhis2-server-tools/deploy/inventory/hosts` and change `SSL_TYPE`  to `customssl` 

To start using a custom certificate instead of the default Letsencrypt
certificate, you need to switch off the certbot service in the `/deploy/inventory/hosts` 
configuration and ensure you have both `fullchain.pem` and `private.pem` files
