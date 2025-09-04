rm(list=ls())

##########################
## Load data

# - run exp-02.py : extract stats to .parquet file
# - set cwd to scripts' dir

library(arrow)
fpath.parquet <- paste(getwd(), "..", "..", "build/exp-02/run-20250902_1727/sil-gap-stats.parquet", sep="/")
df <- read_parquet(fpath.parquet)

rm(fpath.parquet)



##############################################
### Preprocess

# drop rows for 2-ch mix files (direction=="N/A")
df <- df[df$direction != "N/A", ]

df$ch <- NA

df$ch[df$GIM == "GIM" & df$direction == "IN"]   <- "external"
df$ch[df$GIM == "GOUT" & df$direction == "OUT"] <- "external"

df$ch[df$GIM == "GIM" & df$direction == "OUT"] <- "store"
df$ch[df$GIM == "GOUT" & df$direction == "IN"] <- "store"

### Preprocess:: DONE
##############################################

##############################################
### Call durations

df.files <- unique(data.frame(uid=df$uid, GIM=df$GIM, direction=df$direction, sample.size=df$sample.size))
xtabs(~df.files$GIM + df.files$direction)
df.files$dur <- df.files$sample.size / 8000/60

{
  df.plt <- unique(data.frame(uid=df.files$uid, sample.size=df.files$sample.size))
}
{
  trg <- "GOUT"
  df.files.filt <- df.files[df.files$GIM == trg, ]
  df.plt <- unique(data.frame(uid=df.files.filt$uid, sample.size=df.files.filt$sample.size))
}
{
  trg <- "GIM"
  df.files.filt <- df.files[df.files$GIM == trg, ]
  df.plt <- unique(data.frame(uid=df.files.filt$uid, sample.size=df.files.filt$sample.size))
}

call.dur <- df.plt$sample.size / 8000/60
{
  x.max <- 20
  hst <- hist(call.dur, breaks=50, xlab="duration(min)", ylab="Num. of calls", 
#              main="Call duration", 
#              main="Outbound call duration", 
              main="Inbound call duration", 
              xlim=c(0, x.max), ylim=c(0, 70),
              col="lightblue", las=1)
  x.at <- seq(0, x.max, 1)
  abline(v=x.at, col="lightgray")
  x.at <- x.at[!(x.at %in% seq(0, x.max, 5))]
  axis(1, x.at, x.at, cex.axis=0.8, col.axis="gray")
  
  x.at <- seq(0, x.max, 5)
  abline(v=x.at, col="black")
  
  abline(h=seq(0, 80, 5), lty=2, col="gray")
  abline(h=seq(0, 80, 10), col="gray")
  plot(hst, col="lightblue", add=T)
  
  val <- hst$counts
  val[val==0] <- NA
  text(hst$mids, val, val, pos=3, cex=0.66) 
}


rm(df.files, df.plt, call.dur)
### 
##############################################




