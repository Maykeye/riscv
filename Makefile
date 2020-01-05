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
PROOFS=addi ori andi xori


proof: check-proof
	mkdir -p "test_results/${PROOF}"
	python3 rv.py --proof ${PROOF} generate -t il "test_results/${PROOF}/top.il"	
	cp skeleton.sby "test_results/${PROOF}/${PROOF}.sby"		
	cd "test_results/${PROOF}/"  && sby -f "${PROOF}.sby"


PROOF_TARGETS = $(addprefix run-, $(PROOFS))

# https://stackoverflow.com/questions/10172413/how-to-generate-targets-in-a-makefile-by-iterating-over-a-list
define make-proof-target
run-$1: | test_results/$1/$1_bmc/PASS

test_results/$1/$1_bmc/PASS:	
	make proof PROOF=$1	
endef
$(foreach proof,$(PROOFS),$(eval $(call make-proof-target,$(proof))))



run-all-proofs: $(PROOF_TARGETS)


check-proof: 
ifndef PROOF
	$(error PROOF is undefined)
endif

