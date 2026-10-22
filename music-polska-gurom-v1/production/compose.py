"""Original POLSKA GUROM folk/disco sketch. No recordings or external samples.

Render PCM WAV and editable MIDI with Python + numpy + scipy.
"""
from pathlib import Path
import json
import math
import struct
import wave
import zipfile

import numpy as np
from scipy import signal

ROOT = Path(__file__).resolve().parents[1]
SR = 44100
BPM = 120
BEAT = 60 / BPM
RNG = np.random.default_rng(19062026)
TAU = 2 * np.pi
TRACKS = ["accordion", "dulcimer", "bass", "chords", "pad", "brass", "drums"]
PROGRAMS = {"accordion": 21, "dulcimer": 15, "bass": 38, "chords": 21, "pad": 89, "brass": 61}
CHANNELS = {name: n for n, name in enumerate(TRACKS[:-1])} | {"drums": 9}
CHORDS = {
    "Dm": (38, [62, 65, 69]), "Gm": (43, [62, 67, 70]),
    "A": (45, [61, 64, 69]), "Bb": (34, [62, 65, 70]),
    "C": (36, [60, 64, 67]), "F": (41, [60, 65, 69]),
}
PROGRESSION = ["Dm", "Dm", "Gm", "A", "Dm", "Bb", "A", "Dm", "Dm", "C", "Bb", "A", "Gm", "Dm", "A", "A"]

# Written for this project; lengths are in quarter notes. None is a rest.
MELODIES = [
    [(74,.5),(69,.5),(74,.5),(77,.5),(81,1),(77,.5),(76,.5)],
    [(74,1),(77,.5),(79,.5),(81,.75),(None,1.25)],
    [(79,.5),(77,.5),(76,.5),(74,.5),(70,1),(74,1)],
    [(76,.5),(73,.5),(69,1),(76,.5),(73,.5),(None,1)],
    [(74,.5),(77,.5),(81,.75),(None,.25),(77,.5),(74,.5),(69,.5),(74,.5)],
    [(77,.5),(74,.5),(70,.75),(None,.25),(74,.5),(77,.5),(82,.5),(81,.5)],
    [(76,.5),(73,.5),(69,.5),(73,.5),(76,1),(73,.5),(69,.5)],
    [(74,1.5),(None,.5),(69,.5),(72,.25),(73,.25),(74,.5),(None,.5)],
    [(74,.5),(81,.5),(77,.5),(74,.5),(81,.75),(None,1.25)],
    [(76,.5),(79,.5),(84,.75),(None,.25),(79,.5),(76,.5),(72,1)],
    [(77,.5),(74,.5),(70,.5),(74,.5),(77,.75),(None,1.25)],
    [(76,.5),(73,.5),(69,.5),(73,.5),(76,.75),(None,1.25)],
    [(79,.5),(82,.5),(79,.5),(77,.5),(74,.75),(None,.25),(70,.5),(74,.5)],
    [(77,.5),(74,.5),(69,.5),(74,.5),(77,.75),(None,.25),(74,1)],
    [(76,.5),(73,.5),(69,.5),(73,.5),(76,.5),(79,.5),(81,.5),(79,.5)],
    [(76,.75),(73,.25),(69,1),(None,1),(73,.25),(76,.25),(73,.25),(69,.25)],
]


def smooth_gate(t, duration, attack=.012, release=.09):
    return np.minimum(t / attack, 1) * np.clip((duration + release - t) / release, 0, 1)


def hp(noise, cutoff):
    return signal.sosfilt(signal.butter(2, cutoff, "highpass", fs=SR, output="sos"), noise)


def lp(audio, cutoff):
    return signal.sosfilt(signal.butter(2, cutoff, fs=SR, output="sos"), audio, axis=0)


def pitched(instrument, midi, duration):
    f = 440 * 2 ** ((midi - 69) / 12)
    release = {"dulcimer": .72, "bass": .065, "pad": .6, "brass": .12}.get(instrument, .105)
    t = np.arange(int((duration + release) * SR)) / SR
    if instrument in ("accordion", "chords"):
        # Three free reeds, one deliberately almost dry for a natural bellows feel.
        vibrato = .0021 * np.sin(TAU * 5.2 * t) * (1 - np.exp(-t * 7))
        phase = TAU * f * np.cumsum(1 + vibrato) / SR
        out = np.zeros_like(t)
        for ratio, amp in [(.997,.27),(1,.48),(1.003,.25)]:
            for harmonic in range(1, 14):
                if f * harmonic >= SR * .45:
                    break
                strength = harmonic ** -1.25 * (1 if harmonic % 2 else .65)
                out += amp * strength * np.sin(phase * ratio * harmonic + .15 * harmonic)
        out = lp(out, 4300 if instrument == "accordion" else 2500)
        out *= smooth_gate(t, duration, .018, release)
        out *= (.91 + .055 * np.sin(TAU * 2.1 * t))
        return (out * .73).astype(np.float32)
    if instrument == "dulcimer":
        out = np.zeros_like(t)
        for ratio, amp, decay in [(1,1,3.8),(2,.44,5),(3.007,.2,6),(4.016,.1,8),(6.08,.035,11)]:
            out += amp * np.sin(TAU * f * ratio * t) * np.exp(-t * decay)
        out *= np.minimum(t / .0025, 1) * np.clip((duration + release - t) / .04, 0, 1)
        out *= (.6 + .4 * np.exp(-t * 8))
        return (out * .7).astype(np.float32)
    if instrument == "bass":
        phase = TAU * f * (t + .0011 * (1 - np.exp(-t * 55)))
        bright = np.exp(-t * 14)
        out = np.sin(phase) + .34 * np.sin(phase * 2) + bright * (.29*np.sin(phase*3)+.15*np.sin(phase*5))
        out *= smooth_gate(t, duration, .004, release) * (.66 + .34 * np.exp(-t * 13))
        return (out * .75).astype(np.float32)
    if instrument == "pad":
        out = np.zeros_like(t)
        for ratio in [.998, 1.002]:
            out += .45 * np.sin(TAU*f*ratio*t) + .12*np.sin(TAU*f*ratio*2*t)
        out *= smooth_gate(t, duration, .19, release)
        return out.astype(np.float32)
    if instrument == "brass":
        phase = TAU * f * (t + .0005 * np.sin(TAU * 5 * t))
        out = sum(np.sin(phase*k) / k**1.3 for k in range(1,9))
        out = lp(out, 1800 + min(1200, f))
        out *= smooth_gate(t, duration, .022, release)
        return (out * .75).astype(np.float32)
    raise ValueError(instrument)


def percussion(kind):
    duration = {"kick":.43,"clap":.24,"hat":.10,"openhat":.27,"tom":.30,"wood":.09,"crash":1.4}[kind]
    t = np.arange(int(duration * SR)) / SR
    noise = RNG.normal(0, 1, len(t))
    if kind == "kick":
        f = 48 + 100*np.exp(-t*42)
        body = np.sin(TAU*np.cumsum(f)/SR) * np.exp(-t*10)
        click = hp(noise,2200) * np.exp(-t*240) * .075
        out = (body + click) * np.minimum(t/.001,1)
    elif kind == "clap":
        env = np.zeros_like(t)
        for start, amp, decay in [(0,.6,130),(.010,.65,130),(.021,.8,100),(.034,.6,27)]:
            env += np.where(t>=start, amp*np.exp(-np.maximum(t-start,0)*decay),0)
        out = lp(hp(noise,900),8500)*env*.53
        out += .11*np.sin(TAU*180*t)*np.exp(-t*28)
    elif kind in ("hat","openhat"):
        env = np.exp(-t * (75 if kind=="hat" else 17)) * np.minimum(t/.001,1)
        metallic = sum(np.sign(np.sin(TAU*x*t)) for x in [371,517,731,997,1433,2213]) / 6
        out = hp(noise*.72+metallic*.28,6500)*env*.6
    elif kind == "tom":
        out = np.sin(TAU*np.cumsum(105+75*np.exp(-t*30))/SR)*np.exp(-t*15)
        out += lp(noise,2200)*np.exp(-t*40)*.12
    elif kind == "wood":
        out = (np.sin(TAU*890*t)+.6*np.sin(TAU*1475*t))*np.exp(-t*65)*.45
    else:
        out = hp(noise,3500)*np.exp(-t*4.8)*np.minimum(t/.003,1)*.5
    out *= np.minimum((duration-t)/.009,1)
    return out.astype(np.float32)


PERC = {name:percussion(name) for name in ["kick","clap","hat","openhat","tom","wood","crash"]}
DRUM_NOTES = {"kick":36,"clap":39,"hat":42,"openhat":46,"tom":45,"wood":76,"crash":49}


class Song:
    def __init__(self, name, bars, loop=True):
        self.name, self.bars, self.loop = name, bars, loop
        self.seconds = bars*4*BEAT
        self.n = round(self.seconds*SR)
        self.tracks = {k:np.zeros((self.n,2),dtype=np.float32) for k in TRACKS}
        self.events = []

    def add(self, track, midi, beat, length, gain, pan=0, human=0):
        sec = beat*BEAT + human
        duration = length*BEAT
        sound = PERC[midi] if track=="drums" else pitched(track,midi,duration)
        gains = np.array([math.cos((pan+1)*np.pi/4),math.sin((pan+1)*np.pi/4)],dtype=np.float32)
        stereo = sound[:,None] * gains[None,:] * gain
        start = round(sec*SR)
        # Tails crossing the loop edge wrap into its start; nothing is truncated.
        if self.loop:
            cursor=0
            while cursor<len(stereo):
                pos=(start+cursor)%self.n
                count=min(self.n-pos,len(stereo)-cursor)
                self.tracks[track][pos:pos+count] += stereo[cursor:cursor+count]
                cursor += count
        else:
            lo=max(0,start); hi=min(self.n,start+len(stereo))
            if hi>lo: self.tracks[track][lo:hi] += stereo[lo-start:hi-start]
        self.events.append((track,DRUM_NOTES[midi] if track=="drums" else midi,max(0,beat+human/BEAT),length,min(115,max(20,int(gain*230)))))

    def render(self):
        # Gentle four-on-the-floor sidechain in the accompaniment.
        beat_phase=(np.arange(self.n)/SR)%BEAT
        duck=(1-.16*np.exp(-beat_phase*20)).astype(np.float32)
        for key in ["chords","pad","brass"]:
            self.tracks[key] *= duck[:,None]
        dry=sum(self.tracks.values())
        send=(self.tracks["accordion"]*.20+self.tracks["chords"]*.12+self.tracks["dulcimer"]*.28+
              self.tracks["pad"]*.31+self.tracks["brass"]*.18+self.tracks["drums"]*.055)
        wet=np.zeros_like(dry)
        # Short, dark stereo room. The loop uses circular delay; one-shots use linear delay.
        for side in [0,1]:
            for index in range(28):
                delay=.031+index*.0247 + (side*.007 if index%2 else side*.013)
                samples=round(delay*SR)
                amplitude=.11*np.exp(-delay*4.4)*(1 if index%4 else -1)
                source=lp(send[:,1-side] if index%3==0 else send[:,side], 5200-index*110)
                if self.loop:
                    wet[:,side] += np.roll(source,samples)*amplitude
                elif samples<self.n:
                    wet[samples:,side] += source[:-samples]*amplitude
        # Rhythmic stereo echo on folk instruments, kept under the dry attack.
        for delay,gain in [(.375,.10),(.750,.045)]:
            samples=round(delay*SR)
            src=lp((self.tracks["accordion"]+self.tracks["dulcimer"])[:,::-1],4300)
            if self.loop: wet += np.roll(src,samples,axis=0)*gain
            elif samples<self.n: wet[samples:]+=src[:-samples]*gain
        mix=dry+wet
        mix-=np.mean(mix,axis=0)
        # Soft peak compression, then true-peak-conservative level setting.
        mix=np.tanh(mix*1.18)
        truepeak=float(np.max(np.abs(signal.resample_poly(mix,4,1,axis=0))))
        target_peak = -18 if self.name == "06_Czesciowy_zwrot" else -1.5
        mix *= 10**(target_peak/20)/max(truepeak,1e-6)
        if not self.loop:
            fade=min(int(.18*SR),self.n//8)
            mix[-fade:] *= np.linspace(1,0,fade)[:,None]
            mix[:round(.004*SR)] *= np.linspace(0,1,round(.004*SR))[:,None]
        self.audio=mix.astype(np.float32)
        return self.audio


def arrange(name, bonus=False):
    bars=16 if bonus else 32
    song=Song(name,bars)
    for bar in range(bars):
        local=bar%16
        section=bar//8
        chord=PROGRESSION[local]
        root,voicing=CHORDS[chord]
        beat=bar*4
        # Simple disco drums, changing cymbal emphasis between phrases.
        for q in range(4):
            song.add("drums","kick",beat+q,.15,.47 if bonus else .40)
            if q in [1,3]: song.add("drums","clap",beat+q+.008,.12,.30 if bonus else .24,pan=.06)
            song.add("drums","hat",beat+q,.07,.105,pan=-.23)
            song.add("drums","openhat" if (q%2==0 or bonus) else "hat",beat+q+.5,.10,.14 if bonus else .105,pan=.24)
            if bonus:
                song.add("drums","hat",beat+q+.75,.06,.058,pan=-.35)
        if local in [0,8]: song.add("drums","crash",beat,.7,.14 if bonus else .08,pan=.35)
        if local%4==3:
            for offset,vol in [(3.25,.13),(3.5,.17),(3.75,.20)]:
                song.add("drums","tom",beat+offset,.14,vol,pan=(offset-3.5)*1.7)
        if bonus:
            for off in [0,.75,1.5,2,2.75,3.5]: song.add("drums","wood",beat+off,.08,.09,pan=-.4)
        # Bounce from root to octave, with a pickup into the next harmony.
        bass_pattern=[(0,root,.36),(.75,root,.20),(1.5,root+12,.28),(2,root+7,.36),(2.75,root,.22),(3.5,root+12,.25)]
        if bonus: bass_pattern += [(1,root+7,.2),(3.25,root+7,.15)]
        for off,note,dur in bass_pattern:
            song.add("bass",note,beat+off,dur,.255 if bonus else .235)
        # Offbeat accordion stabs have a little intentional bellows stagger.
        for off in [.5,1.5,2.5,3.5]:
            for index,note in enumerate(voicing):
                song.add("chords",note,beat+off,.23,.048 if bonus else .041,pan=-.27+index*.16,human=index*.003)
        for index,note in enumerate(voicing):
            song.add("pad",note-12,beat,3.1,.028 if bonus else .023,pan=-.65+index*.65)
        # Alternate the front instrument, leaving genuine breaths in each phrase.
        front="accordion" if section%2==0 else "dulcimer"
        if bonus: front="accordion"
        position=0
        for ni,(note,dur) in enumerate(MELODIES[local]):
            if note is not None:
                actual=dur*(.76 if front=="accordion" else .67)
                gain=(.115 if front=="accordion" else .105) * (1.03 if ni%3==0 else .94)
                if bonus: gain*=1.04
                song.add(front,note,beat+position,actual,gain,pan=-.09 if front=="accordion" else .22,human=.004*(ni%2))
                if bonus and local in [0,2,4,8,10,12] and ni in [0,4]:
                    song.add("brass",note-12,beat+position,min(actual,.46),.052,pan=.10)
            position+=dur
        # Humorous answering plucks; their density follows fixed arrangement only.
        if local in [1,3,9,11]:
            reply=[voicing[2]+12,voicing[1]+12,voicing[0]+12]
            for j,note in enumerate(reply):
                song.add("dulcimer" if front=="accordion" else "accordion",note,beat+3+j*.25,.17,.072 if bonus else .061,pan=.42)
        if section>=2 and local in [4,6,12,14]:
            for j,note in enumerate(voicing):
                song.add("dulcimer",note+12,beat+2.5+j*.25,.18,.055,pan=.35)
    return song


def stinger(name, mode):
    bars={"trigger":2,"win":1,"big":2,"return":1}[mode]
    song=Song(name,bars,loop=False)
    if mode=="return":
        song.add("dulcimer",62,0,.12,.075)
        return song
    if mode=="trigger":
        notes=[69,73,76,81,74,77,81,86]
        for i,note in enumerate(notes):
            song.add("accordion",note,i*.5,.33,.13,pan=(-.18 if i%2 else .18))
            song.add("dulcimer",note+12,i*.5,.2,.055,pan=.3)
        for off in [0,.75,1.5,2.25,2.75,3,3.25,3.5,3.75]:
            song.add("drums","tom",off,.18,.17+off*.016,pan=-.35+off*.16)
        for note in [62,65,69,74]: song.add("brass",note,4,1.3,.09,pan=(note-68)*.035)
        song.add("bass",38,4,1.7,.3)
        song.add("drums","crash",4,1,.21,pan=.3)
        song.add("drums","kick",4,.2,.42)
    elif mode=="win":
        for i,note in enumerate([74,77,81,86]):
            song.add("dulcimer",note,i*.25,.42,.13,pan=-.20+i*.14)
        for note in [62,65,69]: song.add("accordion",note,.75,.62,.055)
        song.add("bass",38,.75,.7,.13)
    else:
        for i,note in enumerate([74,77,81,86,81,86,89,86]):
            song.add("accordion",note,i*.375,.26,.12,pan=-.15+i*.04)
        for off in [0,1,2,3]:
            song.add("drums","kick",off,.15,.32)
            if off%2: song.add("drums","clap",off,.1,.19)
        for note in [62,65,69,74]:
            song.add("brass",note,3,2,.078,pan=(note-68)*.035)
            song.add("dulcimer",note+12,3,.9,.065)
        song.add("bass",38,3,2,.23)
        song.add("drums","crash",3,1,.18)
    return song


def vlq(value):
    value=int(value)
    out=[value&127]
    while value>>7:
        value>>=7
        out.insert(0,(value&127)|128)
    return bytes(out)


def save_midi(song):
    ppq=480
    chunks=[]
    tempo=b'\x00\xff\x51\x03'+int(60_000_000/BPM).to_bytes(3,'big')
    title=song.name.encode('ascii')
    conductor=b'\x00\xff\x03'+vlq(len(title))+title+tempo+b'\x00\xff\x58\x04\x04\x02\x18\x08'
    conductor+=vlq(song.bars*4*ppq)+b'\xff\x2f\x00'
    chunks.append(conductor)
    for track in TRACKS:
        channel=CHANNELS[track]
        encoded=track.encode()
        data=b'\x00\xff\x03'+vlq(len(encoded))+encoded
        if track in PROGRAMS: data+=bytes([0,0xc0+channel,PROGRAMS[track]])
        events=[]
        for name,note,beat,length,velocity in song.events:
            if name!=track: continue
            onset=round(beat*ppq)
            offset=min(song.bars*4*ppq,round((beat+length)*ppq))
            events.extend([(onset,1,bytes([0x90+channel,note,velocity])),(offset,0,bytes([0x80+channel,note,0]))])
        previous=0
        for tick,_,message in sorted(events,key=lambda e:(e[0],e[1])):
            data+=vlq(tick-previous)+message
            previous=tick
        data+=vlq(max(0,song.bars*4*ppq-previous))+b'\xff\x2f\x00'
        chunks.append(data)
    content=b'MThd'+struct.pack('>IHHH',6,1,len(chunks),ppq)
    for chunk in chunks: content+=b'MTrk'+struct.pack('>I',len(chunk))+chunk
    (ROOT/'midi'/f'{song.name}.mid').write_bytes(content)


def write_wav(path,audio):
    # Triangular dither before 16-bit delivery.
    dither=(RNG.random(audio.shape)-RNG.random(audio.shape))/65536
    pcm=np.clip(np.round((audio+dither)*32767),-32768,32767).astype('<i2')
    with wave.open(str(path),'wb') as handle:
        handle.setnchannels(2); handle.setsampwidth(2); handle.setframerate(SR)
        handle.writeframes(pcm.tobytes())


def metrics(song):
    audio=song.audio
    rms=float(np.sqrt(np.mean(audio**2)))
    peak=float(np.max(np.abs(signal.resample_poly(audio,4,1,axis=0))))
    return {"file":f'wav/{song.name}.wav',"seconds":round(len(audio)/SR,6),"bars":song.bars,"bpm":BPM,
            "loop":song.loop,"sample_rate":SR,"bits":16,"channels":2,
            "true_peak_dbtp_4x":round(20*np.log10(max(peak,1e-10)),3),
            "rms_dbfs":round(20*np.log10(max(rms,1e-10)),3),
            "dc_max":float(np.max(np.abs(np.mean(audio,axis=0)))),
            "loop_boundary_step":float(np.max(np.abs(audio[-1]-audio[0]))) if song.loop else None,
            "finite":bool(np.isfinite(audio).all())}


def main():
    results=[]
    songs={}
    for song in [arrange('01_Karczma_Disco_BASE_120bpm_Dm'),arrange('02_Szarza_Husarza_BONUS_120bpm_Dm',True),
                 stinger('03_Wejscie_do_bonusu','trigger'),stinger('04_Wygrana','win'),
                 stinger('05_Duza_wygrana','big'),stinger('06_Czesciowy_zwrot','return')]:
        print(f'Rendering {song.name}',flush=True)
        audio=song.render()
        write_wav(ROOT/'wav'/f'{song.name}.wav',audio)
        save_midi(song)
        results.append(metrics(song))
        songs[song.name]=song
    base=next(s.audio for s in songs.values() if '_BASE_' in s.name)
    bonus=next(s.audio for s in songs.values() if '_BONUS_' in s.name)
    trigger=songs['03_Wejscie_do_bonusu'].audio
    win=songs['05_Duza_wygrana'].audio
    # 44 s listening demo: 20 s base, 4 s trigger, 16 s bonus, 4 s ending.
    clips=[base[:20*SR].copy(),trigger.copy(),bonus[:16*SR].copy(),win.copy()]
    clips[0][:int(.025*SR)]*=np.linspace(0,1,int(.025*SR))[:,None]
    for i in [0,2]: clips[i][-int(.10*SR):]*=np.linspace(1,0,int(.10*SR))[:,None]
    demo=np.concatenate(clips)
    write_wav(ROOT/'ODSLUCH_FOLK_DISCO_44s.wav',demo)
    (ROOT/'production'/'audio_checks.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps(results,indent=2),flush=True)


if __name__=='__main__':
    main()
