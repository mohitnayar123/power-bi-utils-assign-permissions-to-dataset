# Power BI Utils - Assign Permissions to Datasets
This action provides support for CI/CD of Power BI Reports and Datasets. It assigns permissions to datasets at whenever a dataset is deployed to production workspace.

How to Deploy:
1) Create a config file under **.github/config/** in your repository with the name **deploy_config.yaml**.

```yaml
"Dataset Permissions":
    "<Workspace Name>":
      "group_permissions": {
          "Read": ["b2cfc49a-6f5b-4be4-94e8-af6f31bbdf66"],
          "ReadReshareExplore": ["b2cfc49a-6f5b-4be4-94e8-af6f31bbdf66"]
      }
```


2) Create a workflow under **.github/workflows/** in your repository.
```yaml
name: Workflow Name
on: pull_request
jobs:
  Deploy-Asset:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
        with:
          fetch-depth: 0
      - name: Get changed files
        id: changed-files
        uses: tj-actions/changed-files@v19
        with:
          separator: ","
          quotepath: "false"
      - name: Add group permissions
        uses: mohitnayar123/power-bi-utils-assign-permissions-to-dataset@v1.0.0 # Replace this with the latest version
        with:
          files: ${{ steps.changed-files.outputs.all_modified_files }}
          tenant_id: <put the tenant id here>
          config: .github/config/deploy_config.yaml
          folder: ""
        env:
          CLIENT_ID: ${{ secrets.client_id }}
          CLIENT_SECRET: ${{ secrets.client_secret }}
```
