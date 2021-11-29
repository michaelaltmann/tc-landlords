STORAGE_ACCNT=tclandlords
CONTAINER=tc-landlords-data
DIRECTORY='data/gen'

#az storage fs create -n $CONTAINER --account-name $STORAGE_ACCNT --auth-mode login
#az storage fs directory create -n $DIRECTORY -f $CONTAINER --account-name $STORAGE_ACCNT --auth-mode login

az storage fs file upload -s "$DIRECTORY/clean_grouped_rental_parcels.zip" -p "$DIRECTORY/clean_grouped_rental_parcels.zip"  -f $CONTAINER --account-name $STORAGE_ACCNT --overwrite=true --auth-mode login
az storage fs file upload -s "$DIRECTORY/clean_grouped_rental_parcels.csv" -p "$DIRECTORY/clean_grouped_rental_parcels.csv"  -f $CONTAINER --account-name $STORAGE_ACCNT --overwrite=true --auth-mode login
az storage fs file upload -s "$DIRECTORY/tags.csv" -p "$DIRECTORY/tags.csv"  -f $CONTAINER --account-name $STORAGE_ACCNT --overwrite=true --auth-mode login
az storage fs file upload -s "$DIRECTORY/portfolios.csv" -p "$DIRECTORY/portfolios.csv"  -f $CONTAINER --account-name $STORAGE_ACCNT --overwrite=true --auth-mode login
az storage fs file upload -s "$DIRECTORY/violations.csv" -p "$DIRECTORY/violations.csv"  -f $CONTAINER --account-name $STORAGE_ACCNT --overwrite=true --auth-mode login
az storage fs file list --path $DIRECTORY  -f $CONTAINER --account-name $STORAGE_ACCNT --auth-mode login