pollutantmean <- function(directory, pollutant, id = 1:332) {
	# load the IDs into a list of dataframes
	dflist <- lapply(sprintf("%s/%s/%03i.csv",getwd(),directory,id),read.csv)
	# collapse all frames into a single dataframe
	df <- do.call("rbind",dflist)
	# calculate the mean of the requested pollutant and return to caller
	mean(subset(df, !is.na(sulfate) & !is.na(nitrate) & ID %in% id)[[pollutant]])
}
