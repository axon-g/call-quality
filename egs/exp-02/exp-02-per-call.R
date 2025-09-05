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

rm(hst, trg, val, x.at, x.max)
rm(df.files, df.plt, call.dur, df.files.filt)
### 
##############################################


##############################################
###  Add meta info

# Landline phone 
# 99000000230000000867
# 99000000230000000870
# 99000000230000000873
# 99000000230000000876
# 99000000230000000876

landline <- c("99000000230000000867", "99000000230000000870", 
              "99000000230000000873","99000000230000000876", 
              "99000000230000000876")

#uids <- unique(df$uid)
uids <- df$uid

df.meta <- data.frame(do.call(rbind, strsplit(as.character(uids), "-")))
colnames(df.meta) <- c("date", "time", "phone.1", "phone.2")
df.meta$uid <- uids

df.meta$land <- df.meta$phone.1 %in% landline
bound <- sub("([A-Z]+)([0-9]+)", "\\1", df.meta$phone.2)
df.meta$bound <- NA
df.meta$bound[bound == "GOUT"] = "OUT"
df.meta$bound[bound != "GOUT"] = "IN"
df.meta$phone.2 <- sub("([A-Z]+)([0-9]+)", "\\2", df.meta$phone.2)

#  merge
df <- cbind(df, df.meta)
rm(df.meta, uids, landline, bound)

### Add meta info: DONE 
##############################################

xtabs( ~df$phone.1 + df$bound)
xtabs( ~df$land + df$bound)


df.plt <- df[df$bound =="OUT",]


xtabs(~df.plt$land+df.plt$ch)

##############################################
### Distribution of absolute SIL duration
##############################################
# - does not work with parquett data!

# bp <- barplot(xtabs(~df$zero), col=c("lightblue", "pink"), xlim=c())
# xtabs(~df$zero)

{
  #  trg.call.direction <- "IN"
  {
    trg.ch <- "external"
    trg.zero.type <- "abs"
    trg.zero.type <- "near"
  }
  {
    trg.ch <- "store"
    trg.land <- TRUE  
    trg.zero.type <- "abs"
  }
  {
    trg.ch <- "store"
    trg.land <- FALSE
    trg.zero.type <- "abs"
  }
  
  df.trg <- df.plt[df.plt$zero==trg.zero.type & df.plt$ch==trg.ch & df.plt$land == trg.land, ]
  hst <- hist(df.trg$span.size, breaks=100*1000, plot=F)
  length(hst$mids)
  
  x.min <- min(hst$breaks)
  x.max <- 2000 
  xi.max <- which(hst$breaks == x.max)
  
  hst <- hist(df.trg$span.size, breaks=10000, xlim=c(x.min, x.max), ylim=c(0, 2100),
              ylab="Count", xlab="Duration in frames (800=100ms)", main="",
              col="lightblue"
  )
  title(main=paste0("Distribution of SIL duration (", trg.zero.type, " zero)"))
  mtext(paste0("Channel: ",trg.ch, ", landline: ", trg.land), side=3, line=0.5, cex=0.8, font = 2)
}
{
  # Trend line
  x <- hst$breaks[5:(xi.max*1.2)]+5
  y <- hst$counts[5:(xi.max*1.2)]
  model <- nls(y ~ a / x^2 + b, start = list(a = 1, b = 0))
  pred.y <- predict(model, x)
  
  lines(x, pred.y, lwd=2, col="darkblue")
  
  y.diff <- y - pred.y
  # plot(y.diff)
  # abline(h=0)  
  # abline(h=200, col=2)  
  
  #  x.peak <- c(x[y.diff > 120], 1120)
  #  x.peak <- c(x[y.diff > 200], 1120)  # '1120' visually clear peak
  x.peak <- c(x[y.diff > 300])
  x.peak <- x.peak[x.peak != 325]
  i <- which(x %in% x.peak )
  y.peak <- y[i]
  text(x.peak, y.peak, paste0(floor(1000 * x.peak / 8000), "ms"), col="red", pos=3)
  
  rm(model, pred.y, y.diff, x.peak, y.peak, i)
  rm(hst, df.trg, x, y, x.max, x.min, xi.max)
  rm(trg.call.direction, trg.zero.type,  trg.ch)
}

###
##############################################


##############################################
###  Foreach phone 








df.meta[df.meta$land,c("phone.1", "phone.2", "bound")]

df.meta[df.meta$phone.1 == "0925046839",]

df.meta[,c("phone.1", "phone.2", "bound")]

df.meta$land

df.meta[df.meta$bound == "GOUT",]

df.split$phone.2

summary(df.split)

xtabs(~df.split$phone.1)


xtabs(~df.split$bound)
xtabs(~df.meta$phone.2 + df.meta$bound)

xtabs(~df.meta$phone.1 + df.meta$bound)

xtabs(~df$phone.1 + df.split$bound)

078941575000000023001
^^^^^^^^^^00000023901

xtabs(~phone.2)

          "00000023902001"        
          "00000023901"           
"078941575000000023001" 
"078941575200000023001" 
"078941575000000023002" 
"078941575000000023003"





?do.call
























