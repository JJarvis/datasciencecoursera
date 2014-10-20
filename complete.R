complete <- function(directory, id = 1:332) {
	dflist <- lapply(sprintf("%s/%s/%03i.csv",getwd(),directory,id),read.csv)
	df <- do.call("rbind",dflist)
	dfclean <- subset(df, !is.na(sulfate) & !is.na(nitrate))
	dfclean[["ID"]] <- factor(dfclean[["ID"]], levels=unique(dfclean[["ID"]]))
	by = by(dfclean,dfclean[["ID"]],nrow,simplify=F)
	data.frame(id=names(by),nobs=unlist(by),row.names = NULL)
}
