I need to understand this loop in **ConvertToBin** better
```javascript
        while (loop) {
            let position = position + 1;
            let mask = Main.nextMask(mask);
        
            if (~(position > 16)) {
        
                if (~((value & mask) = 0)) {
                    do Memory.poke(8000 + position, 1);
                   }
                else {
                    do Memory.poke(8000 + position, 0);
                  }    
            }
            else {
                let loop = false;
            }
        }
```

The other `if` says we end on position `15` from range `[0, 15]`. This makes sense because that's what our 16-bit 
system is.

I'm kind of confused as to what `mask` is, but I believe this code takes advantage of the silly fact that all variables are initialized at `0`, so we just have **nextMask** returning consecutive powers of two, which in binary look like this:

```
1        2⁰
10       2¹
100      2²
1000     2³
10000    2⁴
100000   2⁵
```
Here's **nextMask** for reference:
```js
    /** Returns the next mask (the mask that should follow the given mask). */
    function int nextMask(int mask) {
        if (mask = 0) {
            return 1;
        }
        else {
        return mask * 2;
        }
    }
```
When we use the AND operator `&` to AND the mask with the 16-bit value, the result is `0` only if that bit was `0`. Thus if it wasn't `0`, we know the bit value there was `1` and that's why we use **Memory.poke** to set the memory location to `1`
