This script allows you to easily download and install a TU Delft eduVPN OpenVPN configuration on Linux.

## Features
- Retrieves your username, password, and 2FA token from the libsecret keystore, and uses them to generate and download an OpenVPN configuration
- Installs and activates the VPN configuration automatically
- Does not download a new configuration if you already have a valid one installed, and simply activates that one instead
- Automatically removes expired configurations

## Configuration

### Dependencies
```sh
# Selenium is used to download VPN configurations, and PyOTP is used to generate TOTP tokens using your secret
pip3 install selenium pyotp
# libsecret-tools provides secret-tool, which is used to retrieve secrets from the keystore
sudo apt install libsecret-tools
```


### Login details
Add your netid, password, and TOTP secret to the keystore using `secret-tool`.

```sh
printf "yourusernamehere" | secret-tool store --label "TU Delft VPN login" account tudelft type username
printf "yourpasswordhere" | secret-tool store --label "TU Delft VPN login" account tudelft type password username yourusernamehere
printf "yourtotpsecrethere" | secret-tool store --label "TU Delft VPN login" account tudelft type totp username yourusernamehere
```

_Note: the TOTP secret is not a single-use six-digit tokens, it is the key used to generate such tokens. To get it, disable and enable app-based MFA on the TU Delft website, then insert the secret into the keystore before scanning the code with your authenticator app and confirming. Alternatively, you might be able to extract the secret from your existing authenticator app if it allows that._
