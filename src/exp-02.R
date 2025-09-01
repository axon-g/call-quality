rm(list=ls())

# data/exp-02/run-20250901_0843/sil-gap-stats.csv

path.csv = paste(getwd(), "..", "data", "exp-02", "run-20250901_0843", "sil-gap-stats.csv", sep="/")
path.csv = paste(getwd(), "..", "data", "exp-02", "run-20250901_1145", "sil-gap-stats.csv", sep="/")

if (!file.exists(path.csv)) {
  stop("CSV file not found!\n")
}

df <- read.csv(path.csv, sep="\t", header = T)

rm(path.csv)
#xtabs(~df$uid + df$direction)
#xtabs(~df$direction)


##############################################
### Preporcess

xtabs(~df$GIM + df$direction)

# remove diraction "N/A" (no suffixe, 2 channels mixed)
df <- df[df$direction != "N/A", ]

df$ch <- NA

df$ch[df$GIM == "GIM" & df$direction == "IN"]   <- "external"
df$ch[df$GIM == "GOUT" & df$direction == "OUT"] <- "external"

df$ch[df$GIM == "GIM" & df$direction == "OUT"] <- "store"
df$ch[df$GIM == "GOUT" & df$direction == "IN"] <- "store"

### 
##############################################


##############################################
### Call durations

df.files <- unique(data.frame(uid=df$uid, GIM=df$GIM, direction=df$direction, sample.size=df$sample.size))
xtabs(~df.files$GIM + df.files$direction)

df.plt <- unique(data.frame(uid=df.files$uid, sample.size=df.files$sample.size))

call.dur <- df.plt$sample.size / 8000/60
hist(call.dur, breaks=50, xlab="min", main="Call duration", xlim=c(0, 10), col="lightblue", las=1)



rm(df.files, df.plt, call.dur)
### 
##############################################

##############################################
### Distribution of absolute SIL duration
# bp <- barplot(xtabs(~df$zero), col=c("lightblue", "pink"), xlim=c())
# xtabs(~df$zero)

{
#  trg.call.direction <- "IN"
  trg.zero.type <- "abs"
  trg.zero.type <- "near"
  trg.ch <- "external"
  trg.ch <- "store"
  
  df.trg <- df[df$zero==trg.zero.type & df$ch==trg.ch, ]
  hst <- hist(df.trg$span.size, breaks=10000)
  
  x.min <- min(hst$breaks)
  x.max <- 2000 
  xi.max <- which(hst$breaks == x.max)
  
  hst <- hist(df.trg$span.size, breaks=10000, xlim=c(x.min, x.max), ylim=c(0, 1100),
              ylab="Count", xlab="Duration in frames (800=100ms)", main="",
              col="lightblue"
  )
  title(main=paste0("Distribution of SIL duration (", trg.zero.type, " zero)"))
  mtext(paste0("Channel: ",trg.ch), side=3, line=0.5, cex=0.8, font = 2)
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
  x.peak <- c(x[y.diff > 200], 1120)  # '1120' visually clear peak
  i <- which(x %in% x.peak )
  y.peak <- y[i]
  text(x.peak, y.peak, paste0(floor(1000 * x.peak / 8000), "ms"), col="red", pos=3)
  
  rm(model, pred.y, y.diff, x.peak, y.peak, i)
  rm(hst, df.trg, x, y, x.max, x.min, xi.max)
  rm(trg.call.direction, trg.zero.type,  trg.ch)
}


###
##############################################

uid <- sort(unique(df$uid))[32]

hz <- 8000
thresh.ms <- 20
thresh.20 <- thresh.ms * hz / 1000
thresh.ms <- 40
thresh.40 <- thresh.ms * hz / 1000
thresh.ms <- 80
thresh.80 <- thresh.ms * hz / 1000


uids <- sort(unique(df$uid))
chs <- sort(unique(df$ch))
df.stats <- data.frame(uid=length(uids)*length(chs), ch, 
                       sil20=NA, sil40=NA, sil80=NA, sil20p=NA, sil40p=NA, sil80p=NA)
off = 0
for (uid in uids){
  for (ch in chs){
    off = off + 1
    df.stats[off, c("uid", "ch")] <- c(uid, ch)

    df.trg <- df[df$uid == uid & df$ch == ch, ]
    n.sil <- dim(df.trg)[1]
    df.stats[off, "sil"] <- n.sil
    df.stats[off, "sil20"] <- sum(df.trg$span.size >= thresh.20) / n.sil
    df.stats[off, "sil20p"] <- sum(df.trg$span.size >= thresh.20) / n.sil
    df.stats[off, "sil40"] <- sum(df.trg$span.size > thresh.40) / n.sil
    df.stats[off, "sil40p"] <- sum(df.trg$span.size > thresh.40) / n.sil
    df.stats[off, "sil80"] <- sum(df.trg$span.size > thresh.80) / n.sil
    df.stats[off, "sil80p"] <- sum(df.trg$span.size > thresh.80) / n.sil
    
  }
}


###
# Plot differences 
###
library(reshape2)
df.sil20 <- reshape2::dcast(df.stats, uid~ch, value.var="sil20")
df.sil40 <- reshape2::dcast(df.stats, uid~ch, value.var="sil40")
df.sil80 <- reshape2::dcast(df.stats, uid~ch, value.var="sil80")


hist(df.sil20$external-df.sil80$store, breaks=100)
hist(df.sil40$external-df.sil50$store, breaks=100)
hist(df.sil50$external-df.sil50$store, breaks=100)






boxplot(df.stats$sil50~df.stats$ch)
boxplot(df.stats$sil80~df.stats$ch)

plot(NA, xlim=c(0, 0.5), ylim=c(0, .5))
df.plt <- df.stats[df.stats$ch=="store",]
points(df.plt$sil50, df.plt$sil80, col=2)
df.plt <- df.stats[df.stats$ch=="external",]
points(df.plt$sil50, df.plt$sil80, col=1, pch=8)
             
summary(df.stats)

plot(df.plt$sil50)


boxplot(df.sil50$external, df.sil50$store, breaks=100)


ixs <- order(df.sil50$external + df.sil50$store)

plot( seq(1, length(ixs)), df.sil50$external[ixs], type="l", xlim=c(0, 20))
lines(seq(1, length(ixs)), df.sil50$store[ixs],    type="l", col="blue")


plot(NA, xlim=c(0, max(df.sil50$store)), ylim=c(0, max(df.sil50$external)))
points(df.sil50$store, df.sil50$external)

max(df.sil50$external)








  df.ext <- df[df$uid == uid & df$ch == "external", ]
  df.sto <- df[df$uid == uid & df$ch == "store", ]
  
  
  df.ext <- df[df$uid == uid & df$ch == "external", ]
  df.sto <- df[df$uid == uid & df$ch == "store", ]
  df.trg <- rbind(df.ext, df.sto)
  
  n.sil <- dim(df.ext)[1]
  df.stats[i,]$sil50.ext <-  sum(df.ext$span.size > thresh.50) / n.sil
  df.stats[i,]$sil80.ext <-  sum(df.ext$span.size > thresh.80) / n.sil
  
  n.sil <- dim(df.sto)[1]
  df.stats[i,]$sil50.sto <-  sum(df.sto$span.size > thresh.50) / n.sil
  df.stats[i,]$sil50.sto <-  sum(df.sto$span.size > thresh.80) / n.sil
}




for (i in seq(1, length(uids))){ 
  uid <- uids[i]
  
  
  df.ext <- df[df$uid == uid & df$ch == "external", ]
  df.sto <- df[df$uid == uid & df$ch == "store", ]
  df.trg <- rbind(df.ext, df.sto)
  
  n.sil <- dim(df.ext)[1]
  df.stats[i,]$sil50.ext <-  sum(df.ext$span.size > thresh.50) / n.sil
  df.stats[i,]$sil80.ext <-  sum(df.ext$span.size > thresh.80) / n.sil
  
  n.sil <- dim(df.sto)[1]
  df.stats[i,]$sil50.sto <-  sum(df.sto$span.size > thresh.50) / n.sil
  df.stats[i,]$sil50.sto <-  sum(df.sto$span.size > thresh.80) / n.sil
}






for (uid in unique(df$uid)){
  df.ext <- df[df$uid == uid & df$ch == "external", ]
  df.sto <- df[df$uid == uid & df$ch == "store", ]
  df.trg <- rbind(df.ext, df.sto)
  
  n.sil <- dim(df.ext)[1]
  n.longsil <- sum(df.ext$span.size > thresh.frame)
  df.stats[i]$sil50.ext <-  n.longsil / n.sil
  
  n.sil <- dim(df.sto)[1]
  n.longsil <- sum(df.sto$span.size > thresh.frame)
  df.stats[i]$sil50.sto <-  n.longsil / n.sil
}  
  
    
  hist(1000*df.ext$span.size/8000, breaks=100, xlim=c(0, 200))
  hist(1000*df.sto$span.size/8000, breaks=1000, xlim=c(0, 200))
  
  
  
  hist(df.ext$span.size, breaks=10000, xlim=c(0, 100))

  hist(df.trg$span.size, breaks=dim(df.trg)[1]/5, plot=T, xlim=c(0, 1000))
  
    
      df.trg <- rbind(df.ext, df.sto)
  hst <- hist(df.trg$span.size, breaks=dim(df.trg)[1]/5, plot=T)
  i0 <- 2
  i1 <- length(hst$counts)
  y.max <- max(hst$counts[i0:i1])
  y <- hst$counts[i0:i1] / y.max
  x <- log(hst$mids)[i0:i1]
  plot(x, y, type="l", main=uid)
  
  
  #s <- spline(x, y, n = 100) 
  #lines(s$x, s$y, col = "red")

  mdl <- smooth.spline(x, y, spar=0.9)
  y.pred <- predict(mdl, x)
  lines(x, y.pred$y, type="l", col=2)
    
  { # predict for 'store'
    hst.sto <- hist(df.sto$span.size, breaks=hst$breaks, plot=F)
    x <- log(hst.sto$mids)
    y.pred <- predict(mdl, x)$y
    y.ref <-  hst.sto$counts/y.max
    y.diff <- y.pred - y.ref
    max(y.diff)
    min(y.diff)
    sd(y.diff)
#    points(x, y.ref, col=1)
    rm(hst.sto, x, y.ref, y.diff, y.pred)
  }
  {
    hst.ext <- hist(df.ext$span.size, breaks=hst$breaks, plot=F)
    x <- log(hst.ext$mids)
    y.pred <- predict(mdl, x)$y
    y.ref <-  hst.ext$counts/y.max
    y.diff <- y.pred - y.ref
    max(y.diff)
    min(y.diff)
    sd(y.diff)
    #    points(x, y.pred, col=2)
    rm(hst.ext, x, y.ref, y.diff, y.pred)
  }

  
  print(mdl)
  rm(mdl)
}



# sigmoid_model 
mdl <- nls(
  y ~  ymax/(1 + exp(-k*(x - x0))),
  start = list(ymax = 2, x0 = 1, k = -2)
)

mdl <- nls(
  y ~  ymax/(1 + exp(-k*(x - x0))),
  start = list(ymax = 1.032, x0 = 2.969, k = -3.716)
)

mdl <- nls(
  y ~  ymax/(1 + exp(-k*(x - x0))),
  start = list(ymax = 15, x0 = 0, k = -1)
)

lines(x, predict(mdl, x), col=2)





plot(log(hst$mids), log(hst$counts), type="l")

plot(log(hst$mids), hst$counts, type="l")

{
  # fit model using both 'store' and 'external'
  df.trg <- rbind(df.ext, df.sto)
  hst <- hist(df.trg$span.size, breaks=10000, xlim=c(0, 2000), ylim=c(0, 50))
  
  
  y <- hst$counts/ max(hst$counts)
  x <- log(hst$mids)
  
  plot(x, y, type="l")
  
  #sigmoid_model 
  mdl <- nls(
    y ~  ymax/(1 + exp(-k*(x - x0))),
    start = list(ymax = 1.5, x0 = 3, k = -1)
  )
}
{  # predict for store data
  hst.sto <- hist(df.sto$span.size, breaks=hst$breaks, plot=F)
  y.pred <- predict(mdl, log(hst.sto$mids))
  y.ref <-  hst.sto$counts/max(hst.sto$counts)
  y.diff <- y.pred - y.ref
     
  sd(y.diff)
  max(y.diff)
  min(y.diff)
  rm(hst.sto)
}
{
  hst.ext <- hist(df.ext$span.size, breaks=hst$breaks, plot=F)
  y.pred <- predict(mdl, log(hst.ext$mids))
  y.ref <-  hst.ext$counts/max(hst.ext$counts)
  y.diff <- y.pred - y.ref
  sd(y.diff)
  max(y.diff)
  min(y.diff)
  rm(hst.ext)
}




y.pred <- predict(mdl, x)
y.diff <- y - y.pred
lines(x, y.pred, col=2)
plot(y.diff)


plot(log(hst.sto$mids), y.pred, type="l")
y.ref <- hst.sto$counts/max(hst.sto$counts)
points(log(hst.sto$mids), y.ref, col=2)

hist(y.pred - y.ref, breaks=1000)

# features 
# - number of abs zero gaps above 20ms
# - 



##############################################



