import struct,zlib
checked_pngs=set()
def validate_png(file):
 if file in checked_pngs:return
 data=file.read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n','OG is not PNG'
 offset=8;chunks=[];image=b'';header=None
 while offset<len(data):
  assert offset+12<=len(data),'truncated PNG chunk'
  length=struct.unpack('>I',data[offset:offset+4])[0];kind=data[offset+4:offset+8];body=data[offset+8:offset+8+length]
  assert offset+12+length<=len(data),'truncated PNG data'
  crc=struct.unpack('>I',data[offset+8+length:offset+12+length])[0];assert zlib.crc32(kind+body)&0xffffffff==crc,'PNG CRC'
  chunks.append(kind)
  if kind==b'IHDR':
   assert header is None and len(body)==13;header=struct.unpack('>IIBBBBB',body)
  if kind==b'IDAT':image+=body
  offset+=12+length
  if kind==b'IEND':break
 assert chunks[0]==b'IHDR' and chunks[-1]==b'IEND' and offset==len(data),'incomplete PNG'
 width,height,depth,colour,compression,filtering,interlace=header
 assert 600<=width<=8192 and 315<=height<=8192 and compression==filtering==interlace==0
 channels={0:1,2:3,3:1,4:2,6:4};assert colour in channels and depth in [1,2,4,8,16]
 row=(width*channels[colour]*depth+7)//8;decoder=zlib.decompressobj();raw=decoder.decompress(image,(row+1)*height+1)
 assert decoder.eof and len(raw)==(row+1)*height,'PNG decode size'
 assert all(raw[n] in range(5) for n in range(0,len(raw),row+1)),'PNG filter'
 checked_pngs.add(file)
