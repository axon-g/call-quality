//
// drops frames from original wav file
//

#include <iostream>
#include <vector>
#include <fstream>
#include <iostream>
#include <opus/opus.h>
#include <algorithm>

#define DR_WAV_IMPLEMENTATION
#include "dr_wav.h"

/**
 * Reads .wav u-law encoded file into a vector. Hahahaha, 'wav2vec', hahaha.
 * @param wav_file
 * @param pcm
 * @return
 */
int ulaw2vec(const std::string& wav_file, std::vector<int16_t>* pcm){
  drwav wav;
  const char* filename = wav_file.c_str();

  if (!drwav_init_file(&wav, filename, nullptr)) {
    std::cerr << "Failed to open WAV\n";
    return 1;
  }
  if (wav.bitsPerSample != 8) {
    std::cerr << "Only 8-bit PCM WAV files are supported.\n";
    drwav_uninit(&wav);
    return 1;
  }
  if (wav.sampleRate != 8000) {
    std::cerr << "Only 8000 Hz PCM WAV files are supported.\n";
    drwav_uninit(&wav);
    return 1;
  }
  if (wav.channels != 1) {
    std::cerr << "Only mono PCM WAV files are supported.\n";
    drwav_uninit(&wav);
    return 1;
  }

  pcm->resize(wav.totalPCMFrameCount * wav.channels);
  // std::vector<int16_t> pcm(wav.totalPCMFrameCount * wav.channels);
  drwav_uint64 samples_read = drwav_read_pcm_frames_s16__mulaw(&wav, wav.totalPCMFrameCount, pcm->data());
  if (samples_read != wav.totalPCMFrameCount) {
    std::cerr << "Warning: read fewer frames than expected.\n";
  }
  drwav_uninit(&wav);

  return samples_read;
}


int write_dropped(const std::vector<int16_t>& samples, const int frame_size_in_samples, const float& drop_rate, const std::string& out_file) {
  std::ofstream sink(out_file, std::ios::binary);
  if (!sink) {
    std::cerr << "Cannot open file for writing\n";
    return 1;
  }

  int frame_ix = 0; // offset in input

  std::vector<int16_t> zero_frame(frame_size_in_samples, 0);
  int n_dropped = 0;

  srand(time(NULL));
  int left = samples.size();
  int frame_size_in_bytes = 2*frame_size_in_samples;
  while (left > frame_size_in_samples) {
    bool dropped = static_cast<float>(rand())/static_cast<float>(RAND_MAX) <= drop_rate;
    if (dropped) {
      ++n_dropped;
      sink.write(reinterpret_cast<const char*>(zero_frame.data()), frame_size_in_bytes);
    }else {
      sink.write(reinterpret_cast<const char*>(samples.data()) + frame_ix*frame_size_in_bytes, frame_size_in_bytes);
    }
    left -= frame_size_in_samples;
    ++frame_ix;
  }
  if (left > 0) {
    sink.write(reinterpret_cast<const char*>(samples.data()) + frame_ix*frame_size_in_bytes, left* 2);
    ++frame_ix;
  }
  sink.close();
  float perc = 100 * static_cast<float>(n_dropped)/static_cast<float>(frame_ix);
  std::cout << "Dropped " << n_dropped << "/"<< frame_ix << " frames ("<< perc << "%)\n";
  return 0;
}


int main(int argc, char* argv[]) {
  std::string bname = "g_23_sample.ulaw";
  // std::string dpath_decoded = "/home/kinoko/GIT/axon/call-quality/src/exp04/build/decoded-raw/";
  int hz = 8000;
  std::string wav_file = "/home/kinoko/GIT/axon/call-quality/src/exp04/build/encoded/g_23_sample.ulaw.wav";
  std::string dpath_out = "/home/kinoko/GIT/axon/call-quality/src/exp04/build/decoded-raw/";

  std::vector<int16_t> pcm;
  int n_sample = ulaw2vec(wav_file, &pcm);
  int left = n_sample;

  std::vector<int> drop_rates = {0, 10, 20, 30, 40, 50};
  std::vector<int> frame_sizes = {10, 20, 40, 60};  // in ms

  for (const auto& frame_size: frame_sizes) {
    for (const auto& drop_rate_100: drop_rates) {
      std::string fname_dropped = bname + ".frame" + std::to_string(frame_size) + ".drop" + std::to_string(drop_rate_100) +".raw";
      std::string fpath_out = dpath_out + fname_dropped;
      int frame_size_in_samples = (hz/1000)*frame_size;
      float drop_rate = static_cast<float>(drop_rate_100)/100.0;

      std::cout << "Writing: " << fpath_out << std::endl;
      write_dropped(pcm, frame_size_in_samples, drop_rate, fpath_out);
    }
  }
}
