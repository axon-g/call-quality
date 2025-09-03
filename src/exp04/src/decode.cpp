#include <assert.h>
#include <cstring>
#include <fstream>
#include <iostream>
#include <numeric> // for std::accumulate
#include <ogg/ogg.h>
#include <opus/opus.h>
#include <vector>

int do_decode(std::string ogg_file, std::string wav_file, int drop_rate_100, std::vector<int>& drop_mask, int opus_frame_size) {
  srand(time(NULL));

  // Open input Ogg/Opus file
  std::ifstream infile(ogg_file, std::ios::binary);
  if (!infile) {
    std::cerr << "Failed to open: " << ogg_file << std::endl;
    return 1;
  }
  std::cout << "Decoding: " << ogg_file << "; droprate=" << drop_rate_100 << std::endl;

  // prep outfile
  std::ofstream sink(wav_file, std::ios::binary);
  // std::ofstream sink(ogg_file + "_drop=" + std::to_string(drop_rate_100)+ ".raw", std::ios::binary);
  if (!sink) {
    std::cerr << "Cannot open file for writing\n";
    return 1;
  }
  float drop_rate = static_cast<float>(drop_rate_100)/100.0;

  // float drop_rate = static_cast<float>(drop_rate100)/100.0;

  ogg_sync_state   oy; // Sync and verify incoming physical bitstream
  ogg_stream_state os; // Take physical pages, weld into a logical stream
  ogg_page         og; // One Ogg bitstream page
  ogg_packet       op; // One raw packet

  ogg_sync_init(&oy);

  int err_dec;
  OpusDecoder* dec;// = opus_decoder_create(hz, ch, &err);

  char* buffer;
  int   bytes;

  int n_dropped = 0;
  int n_frame = 0;

  bool got_eos = false;
  bool got_id_header = false;
  bool got_tags = false;
  while (!got_eos) {
    // Get a buffer from libogg
    buffer = ogg_sync_buffer(&oy, 4096);
    infile.read(buffer, 4096);
    bytes = infile.gcount();
    ogg_sync_wrote(&oy, bytes);

    // Extract pages
    while (ogg_sync_pageout(&oy, &og) == 1) {
      if (ogg_page_bos(&og)) {
        // Beginning of stream: init stream state
        ogg_stream_init(&os, ogg_page_serialno(&og));
      }
      ogg_stream_pagein(&os, &og);

      // Extract packets from page
      while (ogg_stream_packetout(&os, &op) == 1) {
        if (!got_id_header) { // Parse OpusHead
          if (op.bytes < 8 || memcmp(op.packet, "OpusHead", 8) != 0) {
            std::cerr << "Not an Opus stream!\n";
            return 1;
          }
          int input_ch = op.packet[9];
          uint32_t input_hz = op.packet[12]        |
                             (op.packet[13] << 8)  |
                             (op.packet[14] << 16) |
                             (op.packet[15] << 24) ;
          // std::cout << "Input ch== " << input_ch << " sampling rate=" << input_hz << std::endl;
          dec = opus_decoder_create(input_hz, input_ch, &err_dec);
          if (err_dec != OPUS_OK) {
            std::cerr << "Opus decoder init failed\n";
            return 1;
          }
          got_id_header = true;
          continue;
        }
        if (!got_tags) { // This is the OpusTags packet (skip it)
          got_tags = true;
          continue;
        }

        // Each 'op' is a raw Opus packet
        std::vector<opus_int16> pcm(5760); // 120ms @ 48kHz max
        bool dropped = static_cast<float>(rand())/static_cast<float>(RAND_MAX) <= drop_rate;
        drop_mask.push_back(dropped);

        n_dropped += dropped ? 1 : 0;
        n_frame += 1;
        int decoded_frame_size = -1;
        if (dropped) {
          std::fill(pcm.begin(), pcm.end(), 0);;
          decoded_frame_size = opus_decode(dec, NULL ,0,
                                       pcm.data(),
                                       opus_frame_size,1);
        }else {
          decoded_frame_size = opus_decode(dec,
                                       op.packet,
                                       op.bytes,
                                       pcm.data(),
                                       pcm.size() ,
                                       0);

        }
        if (decoded_frame_size < 0) {
          std::cerr << "Decode error: " << decoded_frame_size << "\n";
        } else {
          // std::cout << "Decoded " << frame_size << " samples, dropped=" << std::boolalpha << dropped  << "\n";
          sink.write(reinterpret_cast<const char*>(pcm.data()), decoded_frame_size*2);
          // TODO: write PCM somewhere (e.g. raw file)
        }
      }
      if (ogg_page_eos(&og)) got_eos = true;
    }
  }

  float perc = 100 * static_cast<float>(n_dropped)/static_cast<float>(n_frame);
  // std::cout << "Dropped " << n_dropped << "/"<< n_frame << " frames ("<< perc << "%)\n";

  // Cleanup
  sink.close();
  infile.close();

  ogg_stream_clear(&os);
  ogg_sync_clear(&oy);
  opus_decoder_destroy(dec);
  return 0;
}



void run() {
  std::string bname = "g_23_sample";
  int hz = 16000;
  std::string dpath_encoded = "/home/kinoko/GIT/axon/call-quality/src/exp04/build/encoded/";
  std::string dpath_decoded = "/home/kinoko/GIT/axon/call-quality/src/exp04/build/decoded-raw/";

  std::vector<int> frame_sizes = {10, 20, 40, 60};  // in ms
  std::vector<int> bitrates = {32, 48, 64};
  std::vector<int> loss_rates = {10, 20, 30, 40, 50, 60, 70, 80, 90};

  std::vector<int> drop_rates = {10, 20, 30, 40, 50};

  for (const auto& frame_size: frame_sizes){
    for (const auto& bitrate: bitrates) {
      for (const auto& loss_rate: loss_rates) {
        std::string fname_opus = bname + ".bitrate" + std::to_string(bitrate) + ".frame" + std::to_string(frame_size) + ".eloss" + std::to_string(loss_rate) +".opus";
        std::string fpath_in  = dpath_encoded + fname_opus;

        for (const auto& drop_rate_100: drop_rates) {
          std::string fname_decoded = bname + ".bitrate" + std::to_string(bitrate) + ".frame" + std::to_string(frame_size) + ".eloss" + std::to_string(loss_rate) + ".drop" + std::to_string(drop_rate_100) +".raw";
          std::string fpath_out = dpath_decoded + fname_decoded;

          std::vector<int> drop_mask;
          int frame_size_in_samples = (hz/1000)*frame_size;
          int status = do_decode(fpath_in, fpath_out, drop_rate_100, drop_mask, frame_size_in_samples);
          assert(status == 0);
        }
        // fname_opus
      }
    }
  }
}

int main(int argc, char* argv[]) {
  // std::string ogg_file = argv[1];
  // std::string wav_file = argv[1];
    run();


  // std::vector<int> drop_rates = {10, 20, 30, 40, 50};
  // for (const auto& drop_rate_100: drop_rates) {
  //   std::cout << std::endl;
  //   std::vector<int> drop_mask;
  //   int status = do_decode(ogg_file, drop_rate_100, drop_mask);
  //
  //   int n_masked = std::accumulate(drop_mask.begin(), drop_mask.end(), 0);
  //   float dropped_actual_ratio = 100.0*static_cast<float>(n_masked)/static_cast<float>(drop_mask.size());
  //   std::cout << "Dropped ratio " << dropped_actual_ratio << " (" <<  drop_rate_100 << "%)" << std::endl;
  // }

  return 0;
}
