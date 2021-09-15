import unittest
import typing as t
import os
import sys
import re
import logging
import zlib

class TestPatching:
    _patches = []


    def __init__(self):
        self._logger = logging.getLogger("DIMMLoader " + str(id(self)))

    def doTest(self):
        #add patches
        with open('/home/pat/devel/arcade/naomi/CANTBoot/cfg/patches/wraptest.binpatch') as pin:
            self.addPatch(pin.read())
            pin.close()

        #run patch
        self.patchROM('/home/pat/devel/arcade/naomi/CANTBoot/roms/mvc2_stock.bin', '/home/pat/devel/arcade/naomi/CANTBoot/roms/patched_wraptest.bin')

        #check files

    '''
    Queue up a binpatch for application during loading
    '''
    def addPatch(self, patchdata : str):
        tmpl = []
        tkeys = []

        #FIXME: THERE'S A WAY MORE EFFICIENT METHOD TO STRUCTURE THIS DATA. FUCK THIS IS DUMB
        for line in patchdata.split('\n'):

            # If it's a comment we don't care about this line
            if len(line) < 1 or line[0] == '#':
                continue
            # Split the line into target address, search bytes, and replace bytes
            print(line)
            e = re.compile("^([A-F0-9]+):\s+([A-F0-9]+)\s+->\s([A-F0-9]+)$").split(line)
            # Make a tuple of the data indexable by the target address, in a dict.
            # Then put it into our temporary list

            tmpl.append({int(e[1], 16): [e[2], e[3]]})
            # Keep track of the target addresses (keys) we use so we can ensure they are sorted properly
            tkeys.append(e[1])

        tmpl.sort(key=lambda d: [k in d for k in tkeys], reverse=True)
        print(tmpl)
        print('------')
        self._patches.append(tmpl)
        print(self._patches)

    def compilePatchData(self) -> dict:

        #TODO: search through patches and find any conflicting addresses/overlaps.
        #for patch in self._patches:
        
        #combine into one large binpatch for more efficient application during rom transfer.
        biglist = [inner for outer in self._patches for inner in outer]

        #return resulting string.
        print(biglist)

        return biglist

    def patchROM(self, name : str, outfile : str, key : str = None, progress_cb = None, chunk_len = 0x8000):
        patchdata = self.compilePatchData()

        data = 'hi' #init with length > 0 so we enter the loop
        patch_start_addr = 0

        crc = 0
        try:
            f_sz = os.stat(name).st_size
            print(f_sz)
            a = open(name, "rb")
        except FileNotFoundError as ex:
            print(ex.repr())
            return
        except Exception as ex:
            print(ex.repr())

        try:
            of = open(outfile, "wb")
        except Exception as ex:
            print(ex.repr())
            return

        addr = 0
        if key:
            d = DES.new(key[::-1], DES.MODE_ECB)

        prg_counter = 0


        #FIXME: PATCHING ROUTINE IS GROSS, REFACTOR IT
        #IT APPEARS TO WORK NOW THOUGH :)

        #TODO: Test patches that extend into multiple chunks


        # Set up our patching flags, bookmarks, and iterators
        patch_continue = 0
        if len(patchdata) < 1:
            # This will make the following loop never check for patch data or attempt to apply any.
            # Because we don't have any patches to apply.
            patched = False
            next_patch = False
        else:
            patched = True #we want to load the first patch on the first iteration
            patch_iter = iter(patchdata)

        #TODO: This is a gross way to track continuations.
        chunk_patches = []
        continues = {}

        while len(data) > 0:

            # patch continue is set to the index of whatever patch data we need to continue on with the next chunk.
            # if zero, we don't need to continue. load the next patch if we have already patched the one we were looking for.

            #get patches for this chunk

            chunk_patch_iter = iter(patchdata)
            #TODO: comment this out for release. no sense in slowing this down with debug output.
            #print("loading next patch.")
            next_patch = next(chunk_patch_iter)
            while next_patch :
                patch_start_addr = list(next_patch.keys())[0]
                #print("%08x1" % patch_start_addr)
                if (patch_start_addr >= addr and patch_start_addr < addr + chunk_len):
                    chunk_patches.append(next_patch)
                    print("adding patch at addr %08x" % patch_start_addr)
                try:
                    next_patch = next(chunk_patch_iter)
                except StopIteration as ex:
                    break
            
            if len(chunk_patches) > 0:
                    patched = False

            #print("%08x\r" % addr)
            data = a.read(0x8000)


            # Only process patch data if:
            # 1. If we have patch data and the start address of the patch is within the chunk we are going to send
            # 2. We have patch data and are continuing a patch from a previous chunk.
            # Algorithm inside this if block is generic to both circumstances.
            #if next_patch:
            #    print("%08x\r" % patch_start_addr)

            #print(addr)

            #print(len(data))
            for chunk_patch in chunk_patches:
                patch_start_addr = list(chunk_patch.keys())[0]
                patch_continue = 0

                if patch_start_addr in dict.keys(continues):
                    patch_continue = continues[patch_start_addr]

                if chunk_patch and ((patch_start_addr  >= addr and patch_start_addr <= addr + chunk_len) or patch_continue > 0):
                    patch_check_val = list(chunk_patch.values())[0][0]
                    chunk_patch_offset = 0

                    #FIXME: the whole patch_continue and patch_offset thing need simplification
                    if patch_continue > 0:
                        print(list(chunk_patch.values())[0][1][patch_continue-1:])
                        patch_bytes = bytes.fromhex(list(chunk_patch.values())[0][1][patch_continue-3:])
                    else:
                        patch_bytes = bytes.fromhex(list(chunk_patch.values())[0][1])

                    chunk_end_addr = addr + chunk_len

                    # do some operations up front to save on processing.
                    #patch_start_addr = next_patch[0]
                    patch_end_addr = patch_start_addr + int(len(patch_bytes)) * 0xff
                    patch_data_length = patch_end_addr - patch_start_addr

                    #truncate working patch to end of chunk
                    if patch_end_addr > chunk_end_addr:
                        patch_bytes = patch_bytes[:-int((patch_end_addr-chunk_end_addr)/0xff)]


                    # patch information solely as far as the current chunk is concerned follows.

                    # if we are not continuing with a patch, patch_continue will be 0, and therefore ignored. Neat!
                    # We're wasting a number of operations the circumstances that A: there is nothing to apply in this chunk and B: patch_continue is 0....
                    # However I am prioritizing readability and maintainability in this project as much as possible.

                    # address to start patching at within this chunk
                    print((0xff * patch_continue))
                    print(patch_continue)
                    chunk_patch_start_addr = int((patch_start_addr - addr) + (0xff * patch_continue))
                    # address to end patching at within this chunk
                    chunk_patch_end_addr = int((patch_start_addr + (0xff * patch_continue)) + (int(len(patch_bytes)) * 0xff) - addr)
                    # length of the data to patch within this chunk
                    chunk_patch_data_length = int(chunk_patch_end_addr - chunk_patch_start_addr)
                    # number of bytes to patch within this chunk
                    chunk_patch_data_nbytes = int(chunk_patch_data_length / 0xff)

                    #TODO: comment these out for release. no sense in slowing this down with debug output.
                    print("patch start %08x end %08x len %08x" % (patch_start_addr, patch_end_addr, patch_data_length))
                    print("chunk start %08x end %08x len %08x" % (addr, chunk_end_addr, chunk_len))
                    print("chunk patch start %08x end %08x len %08x nbytes %x" % (chunk_patch_start_addr, chunk_patch_end_addr, chunk_patch_data_length, chunk_patch_data_nbytes))
                    print("patch check val %s" % patch_check_val)

                    #first run through this patch, sanity-check first byte of input
                    if patch_continue == 0:
                        #print(data[chunk_patch_start_addr])
                        if int(data[chunk_patch_start_addr]) != int(patch_check_val):
                            print('check failed')
                            patched = True

                    # are we patching anything in this chunk?
                    # we need to account for how far through this patch we are.
                    if chunk_patch_start_addr >= (addr - patch_start_addr) + patch_continue and chunk_patch_end_addr <= chunk_end_addr:

                        print('doing it')
                        #we need to patch data in this chunk.
                        byte_idx = int(chunk_patch_start_addr+chunk_patch_offset)

                        barr = bytearray(data)
                        patch_bytes = bytearray(patch_bytes)
                        print(patch_bytes)
                        barr[byte_idx] = patch_bytes[0]

                        data = bytes(barr)
                        #print(len(data))

                        # we need to check if the patch extends beyond this chunk, and if so: how far?
                        if patch_end_addr > chunk_end_addr:

                            # patch continues beyond the end of this chunk. Find out how far, and turn it into an byte-array indexable value.
                            patch_continue = int((patch_end_addr - chunk_end_addr) / 0xff)
                            continues[patch_start_addr] = patch_continue

                            #TODO: comment this out for release. no sense in slowing this down with debug output.
                            print("patch data continues %08x (%d bytes) beyond this chunk" % ((patch_end_addr - chunk_end_addr), patch_continue))
                            i=0
                            for elem in chunk_patches:
                                if list(elem.keys())[0] == patch_start_addr:
                                    #FIXME: THIS IS GROSS SWITCH TO A DICT OF DICT INSTEAD OF A DICT OF LIST
                                    #ALSO JUST REMOVE THE LENGTH OF PATCH_BYTES FROM THE BEGINNING OF THE DATA
                                    print(list(chunk_patches[i].values()))
                                    chunk_patches[i] = {patch_start_addr: [list(chunk_patches[i].values())[0][0], list(chunk_patches[i].values())[0][1][-(patch_continue+1)*2:]]}
                                    print(chunk_patches[i])
                                i+=1

                        else:
                            #TODO: comment these out for release. no sense in slowing this down with debug output.
                            print("patch from %08x done." % patch_start_addr)
                            patched = True
                            patch_continue = 0
                            #remove from patchlist and continuity tracking if applicable
                            if patch_start_addr in dict.keys(continues):
                                i=0
                                for elem in chunk_patches:
                                    if list(elem.keys())[0] == patch_start_addr:
                                        chunk_patches.pop(i)
                                        break
                                    i+=1

                                continues.pop(patch_start_addr)

            #if key:
                #data = d.encrypt(data[::-1])[::-1]

            #self.DIMM_Upload(addr, data, 0)
            of.write(data)

            crc = zlib.crc32(data, crc)
            addr += chunk_len

            # It is faster to use a counter than to do a modulus operation every time we xfer a chunk.
            # Definitely not the biggest bottleneck in this function by any means but I'd like to save where I can
            prg_counter += 1
            if prg_counter > 100:
                if callable(progress_cb):
                    progress_cb(round((addr / f_sz) * 100, 2))
                prg_counter = 0

        print('done')
        of.close()
        a.close()



        crc = ~crc
        #self.DIMM_Upload(addr, "12345678".encode(), 1)
        #self.DIMM_SetInformation(crc, addr)



test = TestPatching()
test.doTest()
