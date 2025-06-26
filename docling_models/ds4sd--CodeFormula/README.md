---
license: mit
---

# Code Formula Model

The **Code Formula Model** processes an image of a code snippet or formula at 120 DPI and outputs its content.

- **Code Snippets**:  
  The model identifies the programming language and outputs the code repsecting the indendation shown in the given image. The output format will be:<br>
  "<\_\<programming language\>\_> \<content of the image\>"<br>
  Example:<br>
  "<_Java_> System.out.println("Hello World.");"

- **Formulas**:  
  The model generates the corresponding LaTeX code.



# References
```
@techreport{Docling,
  author = {Deep Search Team},
  month = {8},
  title = {{Docling Technical Report}},
  url={https://arxiv.org/abs/2408.09869},
  eprint={2408.09869},
  doi = "10.48550/arXiv.2408.09869",
  version = {1.0.0},
  year = {2024}
}

@article{kirillov2023segany,
  title={Segment Anything},
  author={Kirillov, Alexander and Mintun, Eric and Ravi, Nikhila and Mao, Hanzi and Rolland, Chloe and Gustafson, Laura and Xiao, Tete and Whitehead, Spencer and Berg, Alexander C. and Lo, Wan-Yen and Doll{\'a}r, Piotr and Girshick, Ross},
  journal={arXiv:2304.02643},
  year={2023}
}

@misc{zhang2022opt,
      title={OPT: Open Pre-trained Transformer Language Models}, 
      author={Susan Zhang and Stephen Roller and Naman Goyal and Mikel Artetxe and Moya Chen and Shuohui Chen and Christopher Dewan and Mona Diab and Xian Li and Xi Victoria Lin and Todor Mihaylov and Myle Ott and Sam Shleifer and Kurt Shuster and Daniel Simig and Punit Singh Koura and Anjali Sridhar and Tianlu Wang and Luke Zettlemoyer},
      year={2022},
      eprint={2205.01068},
      archivePrefix={arXiv},
      primaryClass={cs.CL}
}

@article{wei2023vary,
  title={Vary: Scaling up the Vision Vocabulary for Large Vision-Language Models},
  author={Wei, Haoran and Kong, Lingyu and Chen, Jinyue and Zhao, Liang and Ge, Zheng and Yang, Jinrong and Sun, Jianjian and Han, Chunrui and Zhang, Xiangyu},
  journal={arXiv preprint arXiv:2312.06109},
  year={2023}
}

@article{wei2024small,
  title={Small Language Model Meets with Reinforced Vision Vocabulary},
  author={Wei, Haoran and Kong, Lingyu and Chen, Jinyue and Zhao, Liang and Ge, Zheng and Yu, En and Sun, Jianjian and Han, Chunrui and Zhang, Xiangyu},
  journal={arXiv preprint arXiv:2401.12503},
  year={2024}
}
```
