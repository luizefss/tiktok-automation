# === CONFIG ==========================================
# Incluir .env se existir
ifneq (,$(wildcard .env))
    include .env
    export
endif

STORYBOARD ?= ../media/storyboard.json
ASSETS_DIR ?= ../media/assets
IMAGES_DIR ?= ../media/images
OUT_VIDEO  ?= ../media/final.mp4
MUSIC_PATH ?=

# Provedor de imagens (openai | leonardo | google)
PROVIDER   ?= openai
IMG_SIZE   ?= 1024x1792

# Chaves/API (lidas do ambiente)
OPENAI_API_KEY   ?= $(shell echo $$OPENAI_API_KEY)
LEONARDO_API_KEY ?= $(shell echo $$LEONARDO_API_KEY)
GOOGLE_API_KEY   ?= $(shell echo $$GOOGLE_API_KEY)
ELEVEN_API_KEY   ?= $(shell echo $$ELEVEN_API_KEY)
ELEVEN_VOICE_ID  ?= Rachel  # voz ElevenLabs

# === REGRAS ==========================================

.PHONY: all images render clean

all: images render

images:
ifeq ($(PROVIDER),openai)
	@if [ -z "$(OPENAI_API_KEY)" ]; then echo "Faltou OPENAI_API_KEY"; exit 1; fi
	python image_fetcher.py \
	  --storyboard $(STORYBOARD) \
	  --outdir $(IMAGES_DIR) \
	  --provider openai \
	  --size $(IMG_SIZE)
endif
ifeq ($(PROVIDER),leonardo)
	@if [ -z "$(LEONARDO_API_KEY)" ]; then echo "Faltou LEONARDO_API_KEY"; exit 1; fi
	python image_fetcher.py \
	  --storyboard $(STORYBOARD) \
	  --outdir $(IMAGES_DIR) \
	  --provider leonardo \
	  --size $(IMG_SIZE)
endif
ifeq ($(PROVIDER),google)
	@if [ -z "$(GOOGLE_API_KEY)" ]; then echo "Faltou GOOGLE_API_KEY"; exit 1; fi
	python image_fetcher.py \
	  --storyboard $(STORYBOARD) \
	  --outdir $(IMAGES_DIR) \
	  --provider google \
	  --size $(IMG_SIZE)
endif

render:
	@if [ -z "$(ELEVEN_API_KEY)" ]; then echo "Faltou ELEVEN_API_KEY"; exit 1; fi
	@if [ -z "$(LEONARDO_API_KEY)" ]; then echo "Faltou LEONARDO_API_KEY"; exit 1; fi
	python render_pipeline_audio_driven.py \
	  --storyboard $(STORYBOARD) \
	  --assets-dir $(ASSETS_DIR) \
	  --images-dir $(IMAGES_DIR) \
	  --out $(OUT_VIDEO) \
	  --music "$(MUSIC_PATH)" \
	  --voice-id $(ELEVEN_VOICE_ID) \
	  --eleven-key $(ELEVEN_API_KEY) \
	  --leonardo-key $(LEONARDO_API_KEY)

clean:
	rm -f $(ASSETS_DIR)/scene_*.mp3 $(ASSETS_DIR)/scene_*.wav $(ASSETS_DIR)/scene_*.mp4
