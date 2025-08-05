param name string
param location string = resourceGroup().location
param tags object = {}
param useExisting bool = false

param sku object = {
  name: 'standard'
}

param authOptions object = {}
param semanticSearch string = 'disabled'

resource search 'Microsoft.Search/searchServices@2021-04-01-preview' = if (!useExisting) {
  name: name
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    authOptions: authOptions
    disableLocalAuth: false
    disabledDataExfiltrationOptions: []
    encryptionWithCmk: {
      enforcement: 'Unspecified'
    }
    hostingMode: 'default'
    networkRuleSet: {
      bypass: 'None'
      ipRules: []
    }
    partitionCount: 1
    publicNetworkAccess: 'Enabled'
    replicaCount: 1
    semanticSearch: semanticSearch
  }
  sku: sku
}

resource existingSearch 'Microsoft.Search/searchServices@2021-04-01-preview' existing = if (useExisting) {
  name: name
}

output id string = useExisting ? existingSearch.id : search.id
output endpoint string = 'https://${name}.search.windows.net/'
output name string = useExisting ? existingSearch.name : search.name
