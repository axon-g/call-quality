#include <iostream>
#include <vector>
#include <fstream>
#include <iostream>
#include <opus/opus.h>

#define DR_WAV_IMPLEMENTATION
#include "dr_wav.h"

/**
 *  Reads .wav file into a vector. Hahahaha, 'wav2vec', hahaha.
 * @param wav_file
 * @param pcm
 * @return
 */
int wav2vec(const std::string& wav_file, std::vector<int16_t>* pcm){
    drwav wav;
    const char* filename = wav_file.c_str();

    if (!drwav_init_file(&wav, filename, nullptr)) {
        std::cerr << "Failed to open WAV\n";
        return 1;
    }
    if (wav.bitsPerSample != 16) {
        std::cerr << "Only 16-bit PCM WAV files are supported.\n";
        drwav_uninit(&wav);
        return 1;
    }
    if (wav.sampleRate != 16000) {
        std::cerr << "Only 16000 Hz PCM WAV files are supported.\n";
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
    drwav_uint64 samples_read = drwav_read_pcm_frames_s16(&wav, wav.totalPCMFrameCount, pcm->data());
    if (samples_read != wav.totalPCMFrameCount) {
        std::cerr << "Warning: read fewer frames than expected.\n";
    }
    drwav_uninit(&wav);
    return samples_read;
}


int main(int argc, char* argv[]) {
    std::string wav_file = argv[1];
    std::cout << "Input WAV: " << wav_file << std::endl;

    int err;
    int hz = 16000;
    int ch = 1;
    int bits = 16;
    OpusEncoder* enc = opus_encoder_create(hz, ch, OPUS_APPLICATION_VOIP, &err);
    if (err != OPUS_OK) {
        std::cerr << "Failed to create encoder: " << opus_strerror(err) << "\n";
        return 1;
    }

    // Valid frame sizes for 8 kHz: 40, 80, 120, 160, 240, 320, 400, 480, 960, 1920, 2880 (these correspond to 5, 10, 15, … ms).

    // Optional: set bitrate
    opus_encoder_ctl(enc, OPUS_SET_BITRATE(32000));  // 32 kbps
    opus_encoder_ctl(enc, OPUS_SET_INBAND_FEC(1));
    opus_encoder_ctl(enc, OPUS_SET_VBR(1));
    opus_encoder_ctl(enc, OPUS_SET_VBR_CONSTRAINT(1));

    // int frame_size = 160; // 10 ms
    int frame_size = 320; // 20 ms

    // input buffer
    opus_int16* padded_frame = (opus_int16*)malloc(frame_size * sizeof(opus_int16));
    if (!padded_frame) return 1; // allocation failed

    // output buffer, must be large enough
    // int max_bytes = 1276;
    std::vector<unsigned char> buff_out(1276);  // max packet size per Opus spec
    // unsigned char* buff_out = (unsigned char*)malloc(max_bytes * sizeof(unsigned char));
    // if (!buff_out) return 1; // allocation failed

    // get the data
    std::vector<int16_t> pcm;
    int n_sample = wav2vec(wav_file, &pcm);
    int left = n_sample;

    std::cout << n_sample << " " << pcm.size() << std::endl;

    // prep outfile
    std::ofstream sink("raw.pcm", std::ios::binary);
    if (!sink) {
        std::cerr << "Cannot open file for writing\n";
        return 1;
    }
    std::ofstream sink_opus("raw.opus", std::ios::binary);
    if (!sink) {
        std::cerr << "Cannot open file for writing\n";
        return 1;
    }

    int frame_ix = 0; // offset in input
    int tot_encoded = 0;
    int tot_written = 0;
    int frame_size_in_bytes = frame_size * bits/8;
    while (left > frame_size) {
        // encode
        int encoded = opus_encode(enc, pcm.data() + frame_size, frame_size, buff_out.data(), sizeof(buff_out));
        if (encoded < 0) {
            printf("Encode error: %s\n", opus_strerror(encoded));
        } else {
            tot_encoded += encoded;
            printf("Encoded %d bytes\n", tot_encoded);

            sink.write(reinterpret_cast<const char*>(pcm.data()) + frame_ix*frame_size_in_bytes, frame_size_in_bytes);
            tot_written += frame_size_in_bytes;
            sink_opus.write(reinterpret_cast<const char*>(buff_out.data()), encoded);
        }
        left -= frame_size;
        ++frame_ix;
    }

    // 149,224 bytes ->  74,612 samples  4.66325 sec
    if (left > 0) { // encode padded
        // padded_frame
        sink.write(reinterpret_cast<const char*>(pcm.data()) + frame_ix*frame_size_in_bytes, left* bits/8);

        // sink_opus.write(reinterpret_cast<const char*>(buff_out.data()), encoded);
        tot_written += left * bits/8;
    }

    // sink.write(reinterpret_cast<const char*>(pcm.data()), pcm.size() * sizeof(int16_t));
    sink.close();
    sink_opus.close();

    std::cout << n_sample << " total written=" << tot_written << std::endl;

    // opus_int32 bitrate;
    // opus_encoder_ctl(enc, OPUS_GET_BITRATE(&bitrate));
    // std::cout << "Default bitrate: " << bitrate << " bps\n";

    return 0;
    std::cout << "Done." << std::endl;
}