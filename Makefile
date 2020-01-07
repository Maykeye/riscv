RV32I_OPS=addi ori andi xori slli srli srai jal jalr lui auipc beq bne blt bge bltu bgeu
PROOFS=$(RV32I_OPS)

PROOF_TARGETS = $(addprefix run-, $(PROOFS))

# https://stackoverflow.com/questions/10172413/how-to-generate-targets-in-a-makefile-by-iterating-over-a-list
define make-proof-target
run-all-proofs: $(PROOF_TARGETS)

run-$1: test_results/$1/$1_bmc/PASS

rerun-$1: 
	rm -f test_results/$1/$1_bmc/PASS
	make -j1 test_results/$1/$1_bmc/PASS

sim-$1:
	python3 rv.py --proof $1

test_results/$1/$1_bmc/PASS: 
	mkdir -p "test_results/$1"
	python3 rv.py --proof $1 generate -t il "test_results/$1/top.il"	
	cp skeleton.sby "test_results/$1/$1.sby"		
	cd "test_results/$1/"  && sby -f "$1.sby"
endef

$(foreach proof,$(PROOFS),$(eval $(call make-proof-target,$(proof))))

clean:
	rm -rf test_results

