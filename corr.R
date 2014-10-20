corr <- function(directory, threshold = 0) {

        corr.by.file <- function(filename) {
            df <- read.csv(filename)
            ngoodrows <- nrow(df[!is.na(df$sulfate) & !is.na(df$nitrate),])
            correlation <- cor(df[["sulfate"]], df[["nitrate"]], use="pairwise.complete.obs")
            c(ngoodrows, correlation)
        }

        filenames <- list.files(directory, full.names=TRUE)
        df <- sapply(filenames, corr.by.file, USE.NAMES=FALSE)
        df[2, df[1,] > threshold]
}
