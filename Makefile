.PHONY: generate proof show ltp

ifeq ($(SRC),)
SRC := core
endif

ifeq ($(MODULE),)
MODULE := core
endif

ifeq ($(PROOF),)
PROOF := reset
endif

ifeq ($(SYNTH),)
LTP_MODULE=$(MODULE)
else
MAKE_SYNTH=synth_$(SYNTH)
LTP_MODULE=
endif
PROOFS=ins_jmp ins_ldaa

