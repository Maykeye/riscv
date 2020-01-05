.PHONY: generate proof show ltp

ifeq ($(SRC),)
SRC := core
endif

ifeq ($(MODULE),)
MODULE := core
endif


ifeq ($(SYNTH),)
LTP_MODULE=$(MODULE)
else
MAKE_SYNTH=synth_$(SYNTH)
LTP_MODULE=
endif
PROOFS=addi


proof: check-proof
	mkdir -p "test_results/${PROOF}"
	python3 rv.py generate -t il "test_results/${PROOF}/top.il"	
	cp skeleton.sby "test_results/${PROOF}/${PROOF}.sby"		
	cd "test_results/${PROOF}/"  && sby -f "${PROOF}.sby"


run-addi:
	make proof PROOF=addi

run-ori:
	make proof PROOF=ori

run-all-proofs: run-addi run-ori


check-proof: 
ifndef PROOF
	$(error ENV is undefined)
endif