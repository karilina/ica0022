# ICA0022 — AWS CLI and EKS access

Before you start, accept the AWS IAM Identity Center invitation email. `kubectl` must already work.

## 1. Install AWS CLI v2

**macOS**
```bash
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o AWSCLIV2.pkg
sudo installer -pkg AWSCLIV2.pkg -target /
```

**Linux / WSL2** (on ARM, use `aarch64` instead of `x86_64`)
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o awscliv2.zip
unzip awscliv2.zip
sudo ./aws/install
```

Check: `aws --version` must print `aws-cli/2.`

## 2. Create the AWS profile

Open the config file:

- macOS/Linux: `mkdir -p ~/.aws && nano ~/.aws/config`

Paste the following and save. If the file already has content, add this at the end.

```ini
[sso-session taltech]
sso_start_url = https://identitycenter.amazonaws.com/ssoins-650816aa11fd1188
sso_region = eu-north-1
sso_registration_scopes = sso:account:access

[profile ica0022]
sso_session = taltech
sso_account_id = 609722444275
sso_role_name = ica0022-students
region = eu-north-1
```

## 3. Log in

```bash
aws sso login --profile ica0022
```

The browser opens, so sign in with your TalTech account. The `Arn` in the output must contain `<uni-id>@taltech.ee`.

```bash
aws sts get-caller-identity --profile ica0022
```

Expect the output to be something similar to this
```
{
    "UserId": "ASDASDASD:larasi@taltech.ee",
    "Account": "609722444275",
    "Arn": "arn:aws:sts::609722444275:assumed-role/AWSReservedSSO_ica0022-students_da92e9b570ea3e15/larasi@taltech.ee"
}
```

## 4. Add the cluster to kubeconfig

Replace `<uni-id>` with your TalTech uni-id:

```bash
aws eks update-kubeconfig --region eu-north-1 --name ica0022 --profile ica0022 --alias ica0022
kubectl config set-context ica0022 --namespace student-<uni-id>
kubectl auth can-i create deployments
```

The last command must print `yes`. Your local context is still available: `kubectl config get-contexts`.

## When it stops working

If `aws` or `kubectl` says the token or session has expired, run `aws sso login --profile ica0022` again.
