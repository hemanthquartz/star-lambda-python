name: Azure Resource Lock Management

on:
  workflow_dispatch:
    inputs:
      action:
        description: 'Action to perform on the management lock'
        required: true
        type: choice
        options:
          - create
          - delete
      resource_group:
        description: 'Resource group to apply the action'
        required: true
        type: choice
        options:
          - splunk-dev-site1-eastus
          - splunk-prod-site1-centralus

jobs:
  manage-lock:
    runs-on: ubuntu-latest

    steps:
      # Checkout code
      - name: Checkout code
        uses: actions/checkout@v3

      # Set environment variables
      - name: Set environment variables
        run: |
          if [ "${{ github.event.inputs.resource_group }}" == "splunk-prod-site1-centralus" ]; then
            echo "SVC_PRINCIPAL=Provider_DevOps_Prod_Splunk_Lock_Mgmt" >> $GITHUB_ENV
          else
            echo "SVC_PRINCIPAL=Provider_DevOps_NonProd_Splunk" >> $GITHUB_ENV
          fi
          echo "LOCK_TYPE=CanNotDelete" >> $GITHUB_ENV
          echo "HOST=splunk.o360.cloud" >> $GITHUB_ENV
          echo "INDEX=oi_pde_devops_observability_prod" >> $GITHUB_ENV
          echo "HEC_TOKEN_SECRET_ID=oi_pde_devops_observability_prod" >> $GITHUB_ENV
          echo "ACTION=${{ github.event.inputs.action }}" >> $GITHUB_ENV
          echo "RESOURCE_GROUP=${{ github.event.inputs.resource_group }}" >> $GITHUB_ENV

      # Log into Azure CLI
      - name: Log into Azure CLI
        env:
          CLIENT_ID: ${{ secrets.CLIENT_ID }}
          CLIENT_SECRET: ${{ secrets.CLIENT_SECRET }}
          TENANT_ID: ${{ secrets.TENANT_ID }}
          SUBSCRIPTION_ID: ${{ secrets.SUBSCRIPTION_ID }}
        run: |
          az login --service-principal -u $CLIENT_ID -p $CLIENT_SECRET --tenant $TENANT_ID
          az account set --subscription $SUBSCRIPTION_ID

      # Create or delete Azure resource management lock
      - name: Create or delete Azure management lock
        if: ${{ env.ACTION == 'create' || env.ACTION == 'delete' }}
        run: |
          if [ "$ACTION" == "create" ]; then
            echo "CREATING lock on resources for resource group $RESOURCE_GROUP"
            az group lock create --lock-type $LOCK_TYPE -n "Resource Group lock created by GitHub Actions" -g $RESOURCE_GROUP
          elif [ "$ACTION" == "delete" ]; then
            echo "DELETING lock on resources for resource group $RESOURCE_GROUP"
            az group lock delete -n "Resource Group lock created by GitHub Actions" -g $RESOURCE_GROUP
          else
            echo "No valid action provided."
            exit 1
          fi

      # Log event to Splunk HEC
      - name: Log event to Splunk HEC
        env:
          PYTHON_VERSION: 3.7
          TOKEN: ${{ secrets.HEC_TOKEN }}
        run: |
          cd python
          pip install -r requirements.txt
          python3 BasicLogging.py -h $HOST -t $TOKEN -i $INDEX -u ${{ github.actor }} -g $RESOURCE_GROUP -l $LOCK_TYPE -a $ACTION